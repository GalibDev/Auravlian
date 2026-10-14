"""Background library operations. No SQL, image decoding or file walks on the UI thread."""
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from auravlian.domain.interfaces.repositories import LibraryPort
from auravlian.domain.models.track import Track

Scanner = Callable[[Iterable[Path], Event, Callable[[str], None]], Iterator[Path]]


@dataclass
class LibraryResult:
    tracks: list[Track] = field(default_factory=list)
    processed: int = 0
    added: int = 0
    warnings: list[str] = field(default_factory=list)
    warning_count: int = 0
    error: str = ""
    cancelled: bool = False


class WorkerSignals(QObject):
    finished = Signal(object)
    progress = Signal(str)


class LibraryWorker(QRunnable):
    def __init__(self, repository: LibraryPort, initialize: Callable[[], None], scanner: Scanner,
                 reader: Callable[[Path], Track], mode: str, paths: list[Path]) -> None:
        super().__init__()
        self.repository, self.initialize = repository, initialize
        self.scanner, self.reader = scanner, reader
        self.mode, self.paths = mode, paths
        self.signals = WorkerSignals()
        self.cancelled = Event()

    def run(self) -> None:
        result = LibraryResult()

        def warning(message: str) -> None:
            result.warning_count += 1
            logging.getLogger("auravlian").warning(json.dumps(message))
            if len(result.warnings) < 100:
                result.warnings.append(message)

        try:
            self.initialize()
            if self.mode != "refresh":
                paths = self.paths
                old = self.repository.tracks() if self.mode == "rescan" else []
                if self.mode == "rescan":
                    paths = self.repository.folders() + [track.path for track in old]
                for path in self.paths:
                    if path.is_dir():
                        self.repository.add_folder(path)
                batch: list[Track] = []
                for path in self.scanner(paths, self.cancelled, warning):
                    if self.cancelled.is_set():
                        break
                    try:
                        batch.append(self.reader(path))
                        result.processed += 1
                    except Exception as exc:
                        warning(f"Skipped {path.name}: {exc}")
                    if len(batch) >= 64:
                        result.added += self.repository.upsert(batch)
                        batch.clear()
                        self.signals.progress.emit(f"Read {result.processed} audio files…")
                if batch:
                    result.added += self.repository.upsert(batch)
                if self.mode == "rescan" and not self.cancelled.is_set():
                    states: list[tuple[Path, bool]] = []
                    for track in old:
                        if self.cancelled.is_set():
                            break
                        try:
                            states.append((track.path, not track.path.is_file()))
                        except OSError as exc:
                            warning(f"Cannot check {track.path.name}: {exc}")
                    if not self.cancelled.is_set():
                        self.repository.mark_missing_batch(states)
            result.tracks = self.repository.tracks()
        except Exception as exc:
            result.error = str(exc)
            logging.getLogger("auravlian").error(json.dumps(f"Library operation failed: {exc}"))
        result.cancelled = self.cancelled.is_set()
        self.signals.finished.emit(result)


class LibraryService(QObject):
    changed = Signal()
    progress = Signal(str)

    def __init__(self, repository: LibraryPort, initialize: Callable[[], None], scanner: Scanner,
                 reader: Callable[[Path], Track], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.repository, self.initialize = repository, initialize
        self.scanner, self.reader = scanner, reader
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.tracks: list[Track] = []
        self.busy = False
        self.status = "Your library starts here. Import local files or a music folder."
        self.last_result = LibraryResult()
        self._worker: LibraryWorker | None = None

    def start(self, mode: str = "refresh", paths: Iterable[Path] = ()) -> bool:
        if self.busy:
            return False
        self.busy = True
        self.status = "Loading library…" if mode == "refresh" else "Scanning local music…"
        worker = LibraryWorker(self.repository, self.initialize, self.scanner, self.reader,
                               mode, list(paths))
        worker.signals.finished.connect(self._finished)
        worker.signals.progress.connect(self._progress)
        self._worker = worker
        self.changed.emit()
        self.pool.start(worker)
        return True

    @Slot(str)
    def _progress(self, message: str) -> None:
        self.status = message
        self.progress.emit(message)

    @Slot(object)
    def _finished(self, result: LibraryResult) -> None:
        self.last_result = result
        if not result.error:
            self.tracks = result.tracks
        self.busy = False
        self._worker = None
        if result.error:
            self.status = f"Library error: {result.error}"
        else:
            prefix = "Cancelled; partial imports saved. " if result.cancelled else ""
            self.status = (f"{prefix}{len(self.tracks)} tracks · {result.added} added · "
                           f"{result.warning_count} warnings")
        self.changed.emit()

    def cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancelled.set()

    def shutdown(self) -> None:
        self.cancel()
        self.pool.waitForDone()
