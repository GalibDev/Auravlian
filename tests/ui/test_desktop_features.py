from pathlib import Path

from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import QSystemTrayIcon

from auravlian.domain.models.track import Track
from auravlian.domain.playback.lyrics import LyricLine
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine


def test_queue_mini_and_fullscreen_share_player(window, qtbot):
    service = window.player_vm.service
    tracks = [Track(Path(f"{i}.wav")) for i in range(3)]
    service.queue.replace(tracks)
    service.changed.emit()
    window.show_queue()
    window.show_mini()
    assert window.queue_panel.vm is window.player_vm
    assert window.mini_player.vm is window.player_vm
    assert window.queue_panel.list.count() == 3
    window.queue_panel.list.setCurrentRow(1)
    window.queue_panel.remove_selected()
    assert len(service.queue.tracks) == 2
    service.clear_queue()
    assert not service.queue.tracks and service.state == "empty"
    window.toggle_fullscreen()
    assert window.isFullScreen() and not window.sidebar.isVisible()
    window.exit_fullscreen()
    assert not window.isFullScreen()


def test_lyrics_highlight_and_device_selection(window):
    page = window.pages["Now Playing"]
    page.lyrics.lines = [LyricLine(0, "First"), LyricLine(1000, "Second")]
    page.render_lyrics()
    window.player_vm.service.on_position(1500)
    assert page.lyric_list.currentRow() == 1
    settings = window.pages["Settings"]
    assert settings.devices.count() == len(QMediaDevices.audioOutputs()) + 1
    engine = window.player_vm.service.audio
    assert isinstance(engine, QtAudioEngine)
    engine.select_device(b"")
    assert engine.selected_device == b""


def test_tray_preference_persistence(window, qtbot, container):
    window.navigate("Settings")
    page = window.pages["Settings"]
    page.tray.setChecked(True)
    assert container.settings.value("desktop/tray", False, type=bool)
    if QSystemTrayIcon.isSystemTrayAvailable():
        window.close()
        assert not window.isVisible()
        window.restore_window()
        assert window.isVisible()
    page.tray.setChecked(False)
