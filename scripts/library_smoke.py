"""Real import/playback smoke in an isolated INI session with generated tagged WAVs."""
import json
from pathlib import Path
import wave

from mutagen.wave import WAVE
from mutagen.id3 import TIT2, TPE1, TALB
from PySide6.QtCore import QSettings, QEventLoop, QTimer
from PySide6.QtTest import QTest

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.presentation.main_window import MainWindow
from auravlian.presentation.pages.library import LibraryPage
from auravlian.shared.events import AppEvents

app = create_application([])
directory = Path("artifacts/library-smoke").resolve()
directory.mkdir(parents=True, exist_ok=True)
music = directory / "generated-media"
music.mkdir(exist_ok=True)
for index, title in enumerate(("Aurora", "Midnight", "Blue Horizon")):
    path = music / f"{index}.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 8000 * 5)
    audio = WAVE(path)
    audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TPE1(encoding=3, text="Smoke Test Artist"))
    audio.tags.add(TALB(encoding=3, text="Generated Test Media"))
    audio.save()
settings = QSettings(str(directory / "session.ini"), QSettings.Format.IniFormat)
container = Container(settings, AppEvents())
window = MainWindow(container)
window.show()
window.navigate("Library")
page = window.pages["Library"]
assert isinstance(page, LibraryPage)
service = page.vm.service


def wait_for(predicate):
    for _ in range(500):
        if predicate():
            return
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
    raise RuntimeError(f"Smoke check timed out: {service.status}")


try:
    wait_for(lambda: not service.busy)
    page.vm.import_paths([music])
    wait_for(lambda: not service.busy)
    assert not service.last_result.error
    assert len(service.tracks) == 3
    QTest.qWait(100)
    window.grab().save(str(directory / "library.png"))
    window.resize(960, 700)
    QTest.qWait(50)
    window.grab().save(str(directory / "library-small.png"))
    window.resize(1440, 900)
    page.search.setText("aurora artist")
    assert page.proxy.rowCount() == 1
    page.table.selectRow(0)
    container.player.service.set_muted(True)
    page.play_selected.click()
    wait_for(lambda: container.player.service.state == "playing")
    assert container.player.title == "Aurora"
    report = {"tracks": len(service.tracks), "search_matches": page.proxy.rowCount(),
              "playback_state": container.player.service.state,
              "playback_title": container.player.title, "status": service.status,
              "database": str(directory / "library/library.sqlite3")}
    (directory / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
finally:
    window.close()
    container.player.service.shutdown()
    service.shutdown()
