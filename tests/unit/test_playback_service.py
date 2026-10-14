import pytest
from PySide6.QtTest import QSignalSpy

from auravlian.application.playback_service import PlaybackService
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.domain.playback.repeat_mode import RepeatMode
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class FakeAudio:
    """Command recorder; never used by the production application."""

    def __init__(self):
        self.loads = []
        self.calls = []

    def load(self, path):
        self.loads.append(path)

    def play(self):
        self.calls.append("play")

    def pause(self):
        self.calls.append("pause")

    def stop(self):
        self.calls.append("stop")

    def seek(self, milliseconds):
        self.calls.append(("seek", milliseconds))

    def set_volume(self, percent):
        self.calls.append(("volume", percent))

    def set_muted(self, muted):
        self.calls.append(("muted", muted))


@pytest.fixture
def playback(qapp, tmp_path):
    files = []
    for name in ("first.wav", "second.wav", "third.wav"):
        path = tmp_path / name
        path.write_bytes(b"isolated command-test input; not real audio")
        files.append(path)
    audio = FakeAudio()
    service = PlaybackService(audio, PlaybackQueue())
    yield service, audio, files
    service.shutdown()


def test_open_deduplicates_and_reports_missing(playback):
    service, audio, files = playback
    errors = QSignalSpy(service.error_raised)
    service.open_files([files[0], files[0], files[1], files[0].parent / "missing.wav"])
    assert len(service.queue.tracks) == 2
    assert audio.loads == [files[0]]
    assert errors.count() == 1
    assert service.state == "loading" and not service.ready


def test_missing_only_preserves_existing_playback(playback):
    service, audio, files = playback
    service.open_files(files)
    service.on_state("playing")
    service.open_files([files[0].parent / "missing.wav"])
    assert service.state == "playing"
    assert audio.loads == [files[0]]
    service.open_files([])
    assert len(service.queue.tracks) == 3


def test_empty_commands_are_safe(playback):
    service, audio, _ = playback
    service.play()
    service.pause()
    service.next()
    service.previous()
    service.seek(100)
    service.stop()
    assert service.state == "empty"
    assert audio.loads == []


def test_play_pause_stop_and_signal_state(playback):
    service, audio, files = playback
    service.open_files(files)
    service.play()  # No duplicate play while loading.
    assert audio.calls == []
    service.on_state("playing")
    service.toggle_play()
    assert audio.calls[-1] == "pause"
    service.on_state("paused")
    service.toggle_play()
    assert audio.calls[-1] == "play"
    service.stop()
    assert service.state == "stopped" and service.position == 0


def test_seek_volume_mute_and_previous_restart(playback):
    service, audio, files = playback
    service.open_files(files)
    service.seek(500)
    assert audio.calls == []
    service.on_ready(True)
    service.on_seekable(True)
    service.on_duration(10_000)
    service.seek(50_000)
    assert audio.calls[-1] == ("seek", 10_000)
    service.on_position(4000)
    service.previous()
    assert audio.calls[-1] == ("seek", 0)
    service.set_volume(120)
    assert service.volume == 100
    service.set_volume(-1)
    assert service.volume == 0
    service.set_muted(True)
    assert audio.calls[-1] == ("muted", True)


@pytest.mark.parametrize("repeat", RepeatMode)
def test_track_completion_and_duplicates(playback, qtbot, repeat):
    service, audio, files = playback
    service.open_files(files[:1])
    service.queue.repeat = repeat
    service.on_state("playing")
    service.on_ended()
    service.on_ended()
    qtbot.wait(10)
    assert len(audio.loads) == (1 if repeat == RepeatMode.OFF else 2)
    if repeat == RepeatMode.OFF:
        assert service.state == "stopped"


def test_completion_advances_and_navigation_cancels_stale_completion(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    service.on_ended()
    qtbot.waitUntil(lambda: len(audio.loads) == 2)
    assert service.queue.current.path == files[1]
    service.on_ended()
    service.open_files(files[:1])
    qtbot.wait(10)
    assert audio.loads[-1] == files[0]


def test_error_skips_once_even_with_repeat_one(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    service.queue.repeat = RepeatMode.ONE
    service.on_error("Corrupt media")
    service.on_error("Duplicate backend error")
    qtbot.waitUntil(lambda: len(audio.loads) == 2)
    assert service.queue.current.path == files[1]
    assert "Corrupt" in service.error_message


def test_all_failed_repeat_all_terminates_and_play_retries(playback, qtbot):
    service, audio, files = playback
    service.open_files(files[:2])
    service.queue.repeat = RepeatMode.ALL
    service.on_error("corrupt first")
    qtbot.waitUntil(lambda: len(audio.loads) == 2)
    service.on_error("corrupt second")
    qtbot.waitUntil(lambda: audio.calls == ["stop"])
    assert service.state == "error"
    qtbot.wait(20)
    assert len(audio.loads) == 2
    service.play()
    assert len(audio.loads) == 3
    assert service.state == "loading"


def test_stop_cancels_pending_recovery(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    service.on_error("corrupt")
    service.stop()
    qtbot.wait(10)
    assert len(audio.loads) == 1
    assert service.state == "stopped"


def test_deleted_next_file_is_skipped(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    files[1].unlink()
    service.next()
    qtbot.waitUntil(lambda: audio.loads[-1] == files[2])
    assert len(audio.loads) == 2


def test_device_error_does_not_skip_files(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    service.on_error("No audio output device is available.")
    qtbot.wait(10)
    assert len(audio.loads) == 1
    assert service.state == "error"


def test_view_model_signals_and_formatting(playback):
    service, _, files = playback
    vm = PlayerViewModel(service)
    changes, errors = QSignalSpy(vm.changed), QSignalSpy(vm.error_raised)
    assert not vm.can_play and vm.title == "Nothing playing"
    service.open_files(files)
    assert vm.title == "first" and not vm.can_play
    service.on_state("paused")
    service.on_position(65_000)
    service.on_duration(125_000)
    assert vm.time_label == "1:05 / 2:05"
    assert vm.can_play
    service.on_error("No audio output device")
    assert errors.count() == 1 and changes.count() >= 5


def test_shutdown_invalidates_callbacks(playback, qtbot):
    service, audio, files = playback
    service.open_files(files)
    service.on_ended()
    service.shutdown()
    qtbot.wait(10)
    assert len(audio.loads) == 1
    assert audio.calls == ["stop"]
