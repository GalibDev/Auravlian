"""Exercise real UI controls and capture actual Qt playback state using isolated WAV media.

Run with --audible for a quiet diagnostic tone; otherwise output stays muted.
This checks backend/UI behavior, not subjective physical speaker sound quality.
"""
import json
import math
from pathlib import Path
import struct
import sys
import wave

from PySide6.QtCore import QSettings, Qt
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtTest import QTest

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.presentation.main_window import MainWindow
from auravlian.shared.events import AppEvents

app = create_application([])
output = Path("artifacts/playback-smoke").resolve()
output.mkdir(parents=True, exist_ok=True)
settings = QSettings(str(output / "settings.ini"), QSettings.Format.IniFormat)
settings.clear()
container = Container(settings, AppEvents())
window = MainWindow(container)
window.show()
service = window.player_vm.service
service.set_volume(15)
service.set_muted("--audible" not in sys.argv)
media = output / "diagnostic-tone.wav"
with wave.open(str(media), "wb") as stream:
    stream.setnchannels(1)
    stream.setsampwidth(2)
    stream.setframerate(16_000)
    stream.writeframes(b"".join(struct.pack("<h", int(1000 * math.sin(
        2 * math.pi * 440 * index / 16_000))) for index in range(16_000 * 8)))
results: dict[str, object] = {"devices": [device.description() for device in QMediaDevices.audioOutputs()],
                              "audible_requested": not service.muted}


def wait_for(predicate, timeout=5000):
    for _ in range(timeout // 20):
        if predicate():
            return
        QTest.qWait(20)
    raise RuntimeError(f"Playback smoke timed out: {service.state}: {service.error_message}")


try:
    service.open_files([media])
    wait_for(lambda: service.ready and service.state == "playing" and service.position > 0)
    results["decode"] = {"state": service.state, "duration_ms": service.duration,
                          "position_ms": service.position}
    window.grab().save(str(output / "playing.png"))
    window.navigate("Now Playing")
    assert window.player_vm is container.player
    QTest.mouseClick(window.playback_bar.buttons["Play"], Qt.MouseButton.LeftButton)
    wait_for(lambda: service.state == "paused")
    service.seek(2500)
    wait_for(lambda: abs(service.position - 2500) < 100)
    results["pause_seek"] = {"state": service.state, "position_ms": service.position}
    window.grab().save(str(output / "paused.png"))
    QTest.mouseClick(window.playback_bar.buttons["Play"], Qt.MouseButton.LeftButton)
    wait_for(lambda: service.state == "playing" and service.position > 2600)
    QTest.mouseClick(window.playback_bar.stop, Qt.MouseButton.LeftButton)
    wait_for(lambda: service.state == "stopped" and service.position == 0)
    results["stop"] = {"state": service.state, "position_ms": service.position}
    results["result"] = "passed"
finally:
    window.close()
    service.shutdown()
    (output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
