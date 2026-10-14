from pathlib import Path
import sqlite3

from auravlian.domain.models.playlist import Playlist, CollectionSnapshot
from auravlian.domain.models.track import Track
from auravlian.infrastructure.database.connection import connection
from auravlian.infrastructure.database.repositories.library_repository import normalized


class CollectionRepository:
    def __init__(self, database: Path) -> None:
        self.database = database

    @staticmethod
    def _name(name: str) -> str:
        name = name.strip()
        if not name or len(name) > 120:
            raise ValueError("Playlist name must contain 1–120 characters.")
        return name

    def create(self, name: str) -> None:
        try:
            with connection(self.database) as db:
                db.execute("INSERT INTO playlists(name) VALUES(?)", (self._name(name),))
        except sqlite3.IntegrityError as exc:
            raise ValueError("A playlist with that name already exists.") from exc

    def rename(self, playlist_id: int, name: str) -> None:
        try:
            with connection(self.database) as db:
                db.execute("UPDATE playlists SET name=? WHERE id=?", (self._name(name), playlist_id))
        except sqlite3.IntegrityError as exc:
            raise ValueError("A playlist with that name already exists.") from exc

    def delete(self, playlist_id: int) -> None:
        with connection(self.database) as db:
            db.execute("DELETE FROM playlists WHERE id=?", (playlist_id,))

    def add(self, playlist_id: int, paths: list[Path]) -> None:
        with connection(self.database) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM playlists WHERE id=?", (playlist_id,)).fetchone() is None:
                raise ValueError("Playlist no longer exists.")
            position = db.execute("SELECT COALESCE(MAX(position),-1)+1 FROM playlist_tracks "
                                  "WHERE playlist_id=?", (playlist_id,)).fetchone()[0]
            for path in paths:
                row = db.execute("SELECT id FROM tracks WHERE path=?", (normalized(path),)).fetchone()
                if row is None:
                    raise ValueError("Import the selected tracks into your library first.")
                cursor = db.execute("INSERT OR IGNORE INTO playlist_tracks VALUES(?,?,?)",
                                    (playlist_id, row[0], position))
                if cursor.rowcount:
                    position += 1

    def remove(self, playlist_id: int, paths: list[Path]) -> None:
        with connection(self.database) as db:
            for path in paths:
                db.execute("DELETE FROM playlist_tracks WHERE playlist_id=? AND track_id IN "
                           "(SELECT id FROM tracks WHERE path=?)", (playlist_id, normalized(path)))

    def reorder(self, playlist_id: int, paths: list[Path]) -> None:
        with connection(self.database) as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT t.id,t.path FROM playlist_tracks p JOIN tracks t ON t.id=p.track_id "
                              "WHERE p.playlist_id=?", (playlist_id,)).fetchall()
            ids = {row["path"]: row["id"] for row in rows}
            keys = [normalized(path) for path in paths]
            if len(keys) != len(ids) or set(keys) != set(ids):
                raise ValueError("The playlist changed. Refresh it before reordering.")
            # Negative temporary positions avoid UNIQUE conflicts during swaps.
            db.execute("UPDATE playlist_tracks SET position=-position-1 WHERE playlist_id=?", (playlist_id,))
            for position, key in enumerate(keys):
                db.execute("UPDATE playlist_tracks SET position=? WHERE playlist_id=? AND track_id=?",
                           (position, playlist_id, ids[key]))

    def favorite(self, paths: list[Path], enabled: bool) -> None:
        with connection(self.database) as db:
            for path in paths:
                row = db.execute("SELECT id FROM tracks WHERE path=?", (normalized(path),)).fetchone()
                if row is None:
                    raise ValueError("Import the selected tracks into your library first.")
                if enabled:
                    db.execute("INSERT OR IGNORE INTO favorites VALUES(?)", (row[0],))
                else:
                    db.execute("DELETE FROM favorites WHERE track_id=?", (row[0],))

    def record_play(self, track: Track) -> None:
        with connection(self.database) as db:
            db.execute("INSERT INTO listening_history(path,title,artist,album,duration_ms,artwork_path) "
                       "VALUES(?,?,?,?,?,?)", (normalized(track.path), track.title, track.artist,
                                               track.album, track.duration_ms, track.artwork_path))

    @staticmethod
    def _history_track(row) -> Track:
        path = Path(row["path"])
        try:
            missing = not path.is_file()
        except OSError:
            missing = True
        return Track(path, row["title"], row["artist"], row["album"], row["duration_ms"],
                     row["artwork_path"], missing)

    def snapshot(self) -> CollectionSnapshot:
        # All reads share one SQLite snapshot, including the library joins.
        with connection(self.database) as db:
            db.execute("BEGIN")
            rows = db.execute("SELECT t.*,a.name artist,b.name album FROM tracks t "
                              "JOIN artists a ON a.id=t.artist_id JOIN albums b ON b.id=t.album_id").fetchall()
            tracks = {r["id"]: Track(Path(r["path"]), r["title"], r["artist"], r["album"],
                                    r["duration_ms"], r["artwork_path"], bool(r["missing"])) for r in rows}
            playlists = []
            for row in db.execute("SELECT * FROM playlists ORDER BY name COLLATE NOCASE"):
                members = db.execute("SELECT track_id FROM playlist_tracks WHERE playlist_id=? "
                                     "ORDER BY position", (row["id"],)).fetchall()
                playlists.append(Playlist(row["id"], row["name"], tuple(tracks[r[0]] for r in members)))
            favorite_ids = {r[0] for r in db.execute("SELECT track_id FROM favorites")}
            favorites = sorted((t for key, t in tracks.items() if key in favorite_ids), key=lambda t: t.title.casefold())
            history_rows = db.execute("SELECT * FROM listening_history WHERE id IN "
                                      "(SELECT MAX(id) FROM listening_history GROUP BY path) "
                                      "ORDER BY id DESC LIMIT 200").fetchall()
            by_path = {normalized(track.path): track for track in tracks.values()}
            history = [by_path[r["path"]] if r["path"] in by_path else self._history_track(r)
                       for r in history_rows]
            count = db.execute("SELECT COUNT(*) FROM listening_history").fetchone()[0]
        return CollectionSnapshot(playlists, favorites, history, count)
