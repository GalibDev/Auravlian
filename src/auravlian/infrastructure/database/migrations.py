from pathlib import Path

from auravlian.infrastructure.database.connection import connection

SCHEMA = (
    "CREATE TABLE artists(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)",
    "CREATE TABLE albums(id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
    "artist_id INTEGER NOT NULL REFERENCES artists(id), UNIQUE(name,artist_id))",
    "CREATE TABLE tracks(id INTEGER PRIMARY KEY, path TEXT NOT NULL UNIQUE, title TEXT NOT NULL, "
    "artist_id INTEGER NOT NULL REFERENCES artists(id), album_id INTEGER NOT NULL REFERENCES albums(id), "
    "duration_ms INTEGER NOT NULL DEFAULT 0, artwork_path TEXT NOT NULL DEFAULT '', "
    "missing INTEGER NOT NULL DEFAULT 0, added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)",
    "CREATE TABLE folders(path TEXT PRIMARY KEY)",
    "CREATE INDEX tracks_artist ON tracks(artist_id)",
    "CREATE INDEX tracks_album ON tracks(album_id)",
    "CREATE INDEX tracks_title ON tracks(title COLLATE NOCASE)",
)


def migrate(path: Path) -> None:
    with connection(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        # Lock before reading the version so concurrent startups cannot both migrate v0.
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise RuntimeError("This library was created by a newer Auravlian version.")
        if version == 0:
            # Explicit BEGIN keeps DDL and the version update in one transaction.
            for statement in SCHEMA:
                db.execute(statement)
            db.execute("PRAGMA user_version=1")
