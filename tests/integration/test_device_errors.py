from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtTest import QSignalSpy

from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine


def test_no_output_device_is_actionable_and_retryable(qapp, qtbot, container, monkeypatch, tmp_path):
    service = container.player.service
    engine = service.audio
    assert isinstance(engine, QtAudioEngine)
    path = tmp_path / "device-test.wav"
    path.write_bytes(b"input not decoded during immediate device validation")
    monkeypatch.setattr(QMediaDevices, "audioOutputs", lambda: [])
    errors = QSignalSpy(service.error_raised)
    service.open_files([path])
    assert errors.count() == 1
    assert service.state == "error" and not service.ready
    assert "No audio output" in service.error_message
    assert container.player.can_play
    service.shutdown()
    engine.deleteLater()
    qtbot.wait(1)


def test_loading_timeout_reports_error(qapp, qtbot, container):
    engine = container.player.service.audio
    assert isinstance(engine, QtAudioEngine)
    errors = QSignalSpy(engine.error)
    engine._load_timeout()
    assert errors.count() == 1
    assert "timed out" in errors.at(0)[0]
    container.player.service.shutdown()
    engine.deleteLater()
    qtbot.wait(1)
