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

COLLECTION_SCHEMA = (
    "CREATE TABLE playlists(id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE)",
    "CREATE TABLE playlist_tracks(playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE, "
    "track_id INTEGER NOT NULL REFERENCES tracks(id), position INTEGER NOT NULL, "
    "PRIMARY KEY(playlist_id,track_id), UNIQUE(playlist_id,position))",
    "CREATE TABLE favorites(track_id INTEGER PRIMARY KEY REFERENCES tracks(id))",
    "CREATE TABLE listening_history(id INTEGER PRIMARY KEY, path TEXT NOT NULL, title TEXT NOT NULL, "
    "artist TEXT NOT NULL, album TEXT NOT NULL, duration_ms INTEGER NOT NULL, artwork_path TEXT NOT NULL, "
    "played_at TEXT NOT NULL DEFAULT(strftime('%Y-%m-%dT%H:%M:%fZ','now')))",
    "CREATE INDEX history_path ON listening_history(path,id)",
)


def migrate(path: Path) -> None:
    with connection(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        # Lock before reading the version so concurrent startups cannot both migrate v0.
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > 2:
            raise RuntimeError("This library was created by a newer Auravlian version.")
        if version == 0:
            # Explicit BEGIN keeps DDL and the version update in one transaction.
            for statement in SCHEMA:
                db.execute(statement)
            db.execute("PRAGMA user_version=1")
        if version < 2:
            for statement in COLLECTION_SCHEMA:
                db.execute(statement)
            db.execute("PRAGMA user_version=2")
