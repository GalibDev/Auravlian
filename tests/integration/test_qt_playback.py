"""Real Qt/FFmpeg playback against generated PCM WAVs, never the user's music."""
import math
import struct
import wave

import pytest
from PySide6.QtCore import QThread
from PySide6.QtMultimedia import QMediaDevices, QMediaPlayer, QAudioOutput
from PySide6.QtTest import QSignalSpy

from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.domain.playback.repeat_mode import RepeatMode


def write_wave(path, duration=3.0):
    rate = 16_000
    frames = bytearray()
    for index in range(int(rate * duration)):
        frames.extend(struct.pack("<h", int(1000 * math.sin(2 * math.pi * 440 * index / rate))))
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(frames)
    return path


@pytest.fixture
def real_playback(qapp, qtbot, container, tmp_path):
    if not QMediaDevices.audioOutputs():
        pytest.skip("Real playback requires an audio output device on this host")
    vm = container.player
    service = vm.service
    engine = service.audio
    assert isinstance(engine, QtAudioEngine)
    service.set_muted(True)
    yield service, engine, tmp_path
    service.shutdown()
    engine.deleteLater()
    qtbot.wait(1)


def test_real_decode_pause_seek_resume_stop(real_playback, qtbot):
    service, engine, folder = real_playback
    wav = write_wave(folder / "actual.wav")
    service.open_files([wav])
    qtbot.waitUntil(lambda: service.state == "playing" and service.ready, timeout=10_000)
    qtbot.waitUntil(lambda: service.position > 0, timeout=5000)
    assert service.duration == 3000
    assert service.seekable
    assert engine.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    service.pause()
    qtbot.waitUntil(lambda: service.state == "paused")
    service.seek(1500)
    qtbot.waitUntil(lambda: abs(service.position - 1500) < 100)
    service.play()
    qtbot.waitUntil(lambda: service.state == "playing")
    service.set_volume(37)
    assert abs(engine.output.volume() - 0.37) < 0.001
    assert engine.output.isMuted()
    service.stop()
    assert service.position == 0
    qtbot.waitUntil(lambda: engine.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState)


def test_real_completion_advances_and_stops(real_playback, qtbot):
    service, engine, folder = real_playback
    first = write_wave(folder / "one.wav", 0.25)
    second = write_wave(folder / "two.wav", 0.25)
    ended = QSignalSpy(engine.ended)
    service.open_files([first, second])
    qtbot.waitUntil(lambda: ended.count() == 2, timeout=10_000)
    qtbot.waitUntil(lambda: service.state == "stopped")
    assert service.queue.current.path == second


def test_real_corrupt_input_recovers_to_valid_media(real_playback, qtbot):
    service, _, folder = real_playback
    corrupt = folder / "broken.mp3"
    corrupt.write_bytes(b"not a supported audio stream")
    valid = write_wave(folder / "valid.wav")
    errors = QSignalSpy(service.error_raised)
    service.open_files([corrupt, valid])
    qtbot.waitUntil(lambda: service.state == "playing" and service.ready, timeout=10_000)
    assert errors.count() >= 1
    assert service.queue.current.path == valid


def test_real_repeat_one_then_manual_next(real_playback, qtbot):
    service, engine, folder = real_playback
    first = write_wave(folder / "repeat.wav", 0.25)
    second = write_wave(folder / "next.wav")
    service.queue.repeat = RepeatMode.ONE
    ended = QSignalSpy(engine.ended)
    service.open_files([first, second])
    qtbot.waitUntil(lambda: ended.count() >= 2, timeout=10_000)
    assert service.queue.current.path == first
    service.next()
    qtbot.waitUntil(lambda: service.queue.current.path == second and service.ready, timeout=5000)


def test_rapid_switching_ends_on_latest_source(real_playback, qtbot):
    service, engine, folder = real_playback
    files = [write_wave(folder / f"switch{index}.wav") for index in range(3)]
    service.open_files(files)
    service.next()
    service.next()
    qtbot.waitUntil(lambda: service.state == "playing" and service.ready, timeout=10_000)
    assert engine.player.source().toLocalFile() == str(files[-1]).replace("\\", "/")
    assert service.queue.current.path == files[-1]


def test_switch_and_stop_immediately_after_seek_resume(real_playback, qtbot):
    service, engine, folder = real_playback
    files = [write_wave(folder / f"stress{index}.wav") for index in range(2)]
    service.open_files(files)
    qtbot.waitUntil(lambda: service.ready and service.state == "playing", timeout=10_000)
    service.pause()
    qtbot.waitUntil(lambda: service.state == "paused")
    service.seek(1000)
    qtbot.waitUntil(lambda: service.position == 1000)
    service.play()
    service.next()
    service.stop()
    qtbot.waitUntil(lambda: engine.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState)
    # A queued old stop cannot stop a subsequent source/play request.
    service.open_files(files[:1])
    qtbot.waitUntil(lambda: service.ready and service.state == "playing", timeout=10_000)
    assert service.queue.current.path == files[0]


def test_singleton_and_owning_thread(qapp, container):
    vm = container.player
    assert container.player is vm
    engine = vm.service.audio
    assert isinstance(engine, QtAudioEngine)
    assert len(engine.findChildren(QMediaPlayer)) == 1
    assert len(engine.findChildren(QAudioOutput)) == 1
    assert engine.thread() == engine.player.thread() == engine.output.thread() == qapp.thread()
    errors = []

    class WrongThread(QThread):
        def run(self):
            try:
                engine.play()
            except RuntimeError as exc:
                errors.append(str(exc))

    thread = WrongThread()
    thread.start()
    assert thread.wait(5000)
    assert errors and "owning Qt thread" in errors[0]
    vm.service.shutdown()
    engine.deleteLater()
