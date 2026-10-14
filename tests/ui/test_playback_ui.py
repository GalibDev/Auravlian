from PySide6.QtCore import QSettings, Qt
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QSignalSpy

from auravlian.presentation.pages.now_playing import NowPlayingPage
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine


def test_all_playback_views_share_one_engine(window):
    vm = window.player_vm
    engine = vm.service.audio
    assert isinstance(engine, QtAudioEngine)
    assert window.playback_bar.vm is vm
    now_playing = window.pages["Now Playing"]
    assert isinstance(now_playing, NowPlayingPage)
    assert now_playing.vm is vm
    for name in window.pages:
        window.navigate(name)
        assert window.container.player is vm
    assert len(engine.findChildren(QMediaPlayer)) == 1


def test_open_dialog_cancel_preserves_queue(window, monkeypatch):
    monkeypatch.setattr("auravlian.presentation.main_window.QFileDialog.getOpenFileNames",
                        lambda *args: ([], ""))
    window.open_files()
    assert not window.player_vm.has_tracks


def test_open_dialog_routes_selected_files(window, monkeypatch, tmp_path):
    path = tmp_path / "selected.wav"
    path.write_bytes(b"corrupt input intentionally used for synchronous routing only")
    monkeypatch.setattr("auravlian.presentation.main_window.QFileDialog.getOpenFileNames",
                        lambda *args: ([str(path)], ""))
    window.open_files()
    assert window.player_vm.service.queue.current.path == path
    window.player_vm.service.stop()


def test_loading_controls_and_backend_signals(window, tmp_path, qtbot):
    vm = window.player_vm
    service = vm.service
    path = tmp_path / "state.wav"
    path.write_bytes(b"command test")
    # Isolate UI state synchronization from codec availability.
    engine = service.audio
    assert isinstance(engine, QtAudioEngine)
    original_load = engine.load
    engine.load = lambda path: None
    try:
        service.open_files([path])
        bar = window.playback_bar
        assert not bar.buttons["Play"].isEnabled()
        assert bar.stop.isEnabled() and not bar.seek.isEnabled()
        engine.state_changed.emit("playing")
        engine.duration_changed.emit(10_000)
        engine.seekable_changed.emit(True)
        engine.ready_changed.emit(True)
        engine.position_changed.emit(2500)
        assert bar.buttons["Play"].text() == "Pause"
        assert bar.seek.isEnabled() and bar.seek.value() == 2500
        assert bar.time.text() == "0:02 / 0:10"
        assert not bar.buttons["Next"].isEnabled()
        changes = QSignalSpy(vm.changed)
        qtbot.mouseClick(bar.buttons["Shuffle"], Qt.MouseButton.LeftButton)
        assert service.queue.shuffle
        qtbot.mouseClick(bar.buttons["Repeat"], Qt.MouseButton.LeftButton)
        assert bar.buttons["Repeat"].text() == "Repeat: one"
        bar.volume.setValue(24)
        qtbot.mouseClick(bar.mute, Qt.MouseButton.LeftButton)
        assert service.volume == 24 and service.muted
        assert changes.count() >= 4
    finally:
        engine.load = original_load


def test_audio_preferences_persist_without_position_writes(window, container):
    service = window.player_vm.service
    service.set_volume(29)
    service.set_muted(True)
    container.settings.sync()
    reread = QSettings(container.settings.fileName(), QSettings.Format.IniFormat)
    assert reread.value("audio/volume", type=int) == 29
    assert reread.value("audio/muted", type=bool) is True


def test_missing_file_error_visible_in_both_views(window, tmp_path):
    window.player_vm.service.open_files([tmp_path / "missing.wav"])
    assert "File not found" in window.playback_bar.caption.text()
    page = window.pages["Now Playing"]
    assert isinstance(page, NowPlayingPage)
    assert page.status.text() == window.playback_bar.caption.text()
