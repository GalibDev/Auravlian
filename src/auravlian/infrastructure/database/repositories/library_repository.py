import os
from pathlib import Path
from collections.abc import Iterable

from auravlian.domain.models.track import Track
from auravlian.infrastructure.database.connection import connection


def normalized(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


class LibraryRepository:
    def __init__(self, database: Path) -> None:
        self.database = database

    def upsert(self, tracks: Iterable[Track]) -> int:
        added = 0
        with connection(self.database) as db:
            for track in tracks:
                db.execute("INSERT OR IGNORE INTO artists(name) VALUES(?)", (track.artist,))
                artist = db.execute("SELECT id FROM artists WHERE name=?", (track.artist,)).fetchone()[0]
                db.execute("INSERT OR IGNORE INTO albums(name,artist_id) VALUES(?,?)", (track.album, artist))
                album = db.execute("SELECT id FROM albums WHERE name=? AND artist_id=?",
                                   (track.album, artist)).fetchone()[0]
                path = normalized(track.path)
                added += int(db.execute("SELECT 1 FROM tracks WHERE path=?", (path,)).fetchone() is None)
                db.execute(
                    "INSERT INTO tracks(path,title,artist_id,album_id,duration_ms,artwork_path,missing) "
                    "VALUES(?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET title=excluded.title, "
                    "artist_id=excluded.artist_id,album_id=excluded.album_id,duration_ms=excluded.duration_ms, "
                    "artwork_path=excluded.artwork_path,missing=excluded.missing",
                    (path, track.title, artist, album, track.duration_ms, track.artwork_path, track.missing))
        return added

    def tracks(self) -> list[Track]:
        with connection(self.database) as db:
            rows = db.execute(
                "SELECT t.*,a.name AS artist,b.name AS album FROM tracks t "
                "JOIN artists a ON a.id=t.artist_id JOIN albums b ON b.id=t.album_id "
                "ORDER BY t.title COLLATE NOCASE,t.id").fetchall()
        return [Track(Path(r["path"]), r["title"], r["artist"], r["album"], r["duration_ms"],
                      r["artwork_path"], bool(r["missing"])) for r in rows]

    def add_folder(self, path: Path) -> None:
        with connection(self.database) as db:
            db.execute("INSERT OR IGNORE INTO folders(path) VALUES(?)", (normalized(path),))

    def folders(self) -> list[Path]:
        with connection(self.database) as db:
            return [Path(r[0]) for r in db.execute("SELECT path FROM folders ORDER BY path")]

    def mark_missing(self, path: Path, missing: bool) -> None:
        self.mark_missing_batch([(path, missing)])

    def mark_missing_batch(self, states: list[tuple[Path, bool]]) -> None:
        with connection(self.database) as db:
            db.executemany("UPDATE tracks SET missing=? WHERE path=?",
                           [(missing, normalized(path)) for path, missing in states])
