"""Visual smoke of the final desktop controls; generated, muted audio only."""
from pathlib import Path
import math
import struct
import wave

from PySide6.QtCore import QSettings, QTimer

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.domain.models.track import Track
from auravlian.presentation.main_window import MainWindow
from auravlian.shared.events import AppEvents

app = create_application([])
output = Path("artifacts/desktop-preview").resolve()
output.mkdir(parents=True, exist_ok=True)
audio = output / "Aurora tone.wav"
with wave.open(str(audio), "wb") as stream:
    stream.setnchannels(1)
    stream.setsampwidth(2)
    stream.setframerate(16000)
    stream.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(
        2 * math.pi * 440 * index / 16000))) for index in range(16000 * 5)))
audio.with_suffix(".lrc").write_text("[00:00]A local sound, a little closer.\n[00:01]Feel beyond sound.", encoding="utf-8")
container = Container(QSettings(str(output / "session.ini"), QSettings.Format.IniFormat), AppEvents())
window = MainWindow(container)
window.navigate("Now Playing")
window.show()
container.player.service.set_muted(True)
container.player.service.open_tracks([Track(audio, "Aurora tone", "Generated test audio")])
timer = QTimer()


def capture():
    if container.player.service.position < 700:
        return
    timer.stop()
    window.grab().save(str(output / "now-playing.png"))
    window.show_mini()
    window.mini_player.grab().save(str(output / "mini-player.png"))
    window.show_queue()
    window.queue_panel.grab().save(str(output / "queue.png"))
    window.quit_application()


timer.timeout.connect(capture)
timer.start(50)
QTimer.singleShot(12000, window.quit_application)
app.exec()
