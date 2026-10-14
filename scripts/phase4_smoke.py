"""Phase 4 UI/persistence smoke using isolated real local WAV files."""
import json
from pathlib import Path
import wave

from PySide6.QtCore import QEventLoop, QSettings, QTimer

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.domain.models.track import Track
from auravlian.presentation.main_window import MainWindow
from auravlian.presentation.pages.collections import CollectionPage
from auravlian.shared.events import AppEvents

app = create_application([])
directory = Path("artifacts/phase4-smoke").resolve()
directory.mkdir(parents=True, exist_ok=True)
settings = QSettings(str(directory / "session.ini"), QSettings.Format.IniFormat)
container = Container(settings, AppEvents())
window = MainWindow(container)
window.show()
library = container.library.service
collections = container.collections.service


def wait_for(predicate):
    for _ in range(500):
        if predicate():
            return
        loop = QEventLoop()
        QTimer.singleShot(20, loop.quit)
        loop.exec()
    raise RuntimeError(f"Phase 4 smoke timed out: {collections.error}")


def ready():
    wait_for(lambda: not library.busy and not collections.busy)
    assert not collections.error


try:
    ready()
    tracks = []
    for index, title in enumerate(("Aurora", "Midnight", "Blue Horizon")):
        path = directory / f"phase4-{index}.wav"
        with wave.open(str(path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(8000)
            stream.writeframes(b"\x00\x00" * 8000 * 5)
        tracks.append(Track(path, title, "Smoke Test Artist", "Generated Test Album", 5000))
    # This fixture seeds metadata explicitly; the smoke targets Phase 4, not import.
    library.repository.upsert(tracks)
    library.start()
    ready()
    if not collections.snapshot.playlists:
        collections.create("Evening Sessions")
        ready()
    playlist_id = collections.snapshot.playlists[0].id
    collections.add(playlist_id, [t.path for t in tracks])
    collections.reorder(playlist_id, [t.path for t in reversed(tracks)])
    collections.favorite([tracks[0].path], True)
    ready()
    container.player.service.set_muted(True)
    container.player.service.open_tracks([tracks[0]])
    previous_count = collections.snapshot.play_count
    wait_for(lambda: collections.snapshot.play_count > previous_count)
    container.player.service.pause()
    wait_for(lambda: container.player.service.state == "paused")
    for name in ("Playlists", "Albums", "Artists", "Favorites", "Recently Played"):
        window.navigate(name)
        page = window.pages[name]
        assert isinstance(page, CollectionPage)
        app.processEvents()
        window.grab().save(str(directory / (name.lower().replace(" ", "-") + ".png")))
    window.navigate("Playlists")
    window.resize(960, 700)
    app.processEvents()
    window.grab().save(str(directory / "playlists-small.png"))
    report = {"playlists": len(collections.snapshot.playlists),
              "playlist_order": [t.title for t in collections.snapshot.playlists[0].tracks],
              "favorites": len(collections.snapshot.favorites),
              "recent_tracks": [t.title for t in collections.snapshot.history],
              "actual_playback_starts": collections.snapshot.play_count,
              "result": "passed"}
    (directory / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
finally:
    window.close()
    container.player.service.shutdown()
    library.shutdown()
    collections.shutdown()
