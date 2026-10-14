"""Serialized background collection writes and immutable UI snapshots."""
from collections.abc import Callable
import json
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from auravlian.domain.interfaces.repositories import CollectionPort
from auravlian.domain.models.playlist import CollectionSnapshot
from auravlian.domain.models.track import Track
from auravlian.domain.interfaces.repositories import LibraryPort
from auravlian.application.playlist_io import read_m3u, write_m3u


class CollectionSignals(QObject):
    finished = Signal(object, str)


class CollectionJob(QRunnable):
    def __init__(self, repository: CollectionPort, initialize: Callable[[], None],
                 action: Callable[[], None]) -> None:
        super().__init__()
        self.repository, self.initialize, self.action = repository, initialize, action
        self.signals = CollectionSignals()

    def run(self) -> None:
        try:
            self.initialize()
            self.action()
            self.signals.finished.emit(self.repository.snapshot(), "")
        except Exception as exc:
            logging.getLogger("auravlian").error(json.dumps(f"Collection operation failed: {exc}"))
            self.signals.finished.emit(None, str(exc))


class PlaylistService(QObject):
    changed = Signal()

    def __init__(self, repository: CollectionPort, initialize: Callable[[], None],
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.repository, self.initialize = repository, initialize
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.snapshot = CollectionSnapshot()
        self.error = ""
        self._jobs: list[CollectionJob] = []
        self._closed = False

    @property
    def busy(self) -> bool:
        return bool(self._jobs)

    def _submit(self, action: Callable[[], None]) -> None:
        if self._closed:
            return
        job = CollectionJob(self.repository, self.initialize, action)
        job.signals.finished.connect(self._finished)
        self._jobs.append(job)
        self.changed.emit()
        self.pool.start(job)

    @Slot(object, str)
    def _finished(self, snapshot: CollectionSnapshot | None, error: str) -> None:
        self._jobs.pop(0)
        if snapshot is not None:
            self.snapshot = snapshot
        self.error = error
        self.changed.emit()

    def refresh(self) -> None:
        self._submit(lambda: None)

    def create(self, name: str) -> None:
        self._submit(lambda: self.repository.create(name))

    def rename(self, playlist_id: int, name: str) -> None:
        self._submit(lambda: self.repository.rename(playlist_id, name))

    def delete(self, playlist_id: int) -> None:
        self._submit(lambda: self.repository.delete(playlist_id))

    def add(self, playlist_id: int, paths: list[Path]) -> None:
        self._submit(lambda: self.repository.add(playlist_id, paths))

    def remove(self, playlist_id: int, paths: list[Path]) -> None:
        self._submit(lambda: self.repository.remove(playlist_id, paths))

    def reorder(self, playlist_id: int, paths: list[Path]) -> None:
        self._submit(lambda: self.repository.reorder(playlist_id, paths))

    def favorite(self, paths: list[Path], enabled: bool) -> None:
        self._submit(lambda: self.repository.favorite(paths, enabled))

    def record(self, track: Track) -> None:
        self._submit(lambda: self.repository.record_play(track))

    def import_m3u(self, path: Path, library: LibraryPort, reader: Callable[[Path], Track]) -> None:
        def action() -> None:
            tracks = [reader(media) for media in read_m3u(path)]
            if not tracks:
                raise ValueError("Playlist contains no local tracks.")
            existing = {p.name.casefold() for p in self.repository.snapshot().playlists}
            name = path.stem[:100] or "Imported playlist"
            base, suffix = name, 2
            while name.casefold() in existing:
                name = f"{base} ({suffix})"
                suffix += 1
            library.upsert(tracks)
            self.repository.create(name)
            playlist = next(p for p in self.repository.snapshot().playlists if p.name == name)
            self.repository.add(playlist.id, [t.path for t in tracks])
        self._submit(action)

    def export_m3u(self, playlist_id: int, path: Path) -> None:
        def action() -> None:
            playlist = next(p for p in self.repository.snapshot().playlists if p.id == playlist_id)
            write_m3u(path, playlist.tracks)
        self._submit(action)

    def shutdown(self) -> None:
        self._closed = True
        self.pool.waitForDone()
