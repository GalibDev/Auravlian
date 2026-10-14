from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from auravlian.domain.playback.lyrics import parse_lrc, LyricLine


class LyricsSignals(QObject):
    finished = Signal(str, object, str)


class LyricsJob(QRunnable):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.signals = LyricsSignals()

    def run(self) -> None:
        path = self.path.with_suffix(".lrc")
        try:
            if not path.is_file():
                self.signals.finished.emit(str(self.path), [], "No local .lrc lyrics file found.")
                return
            if path.stat().st_size > 1_000_000:
                raise ValueError("Lyrics file is larger than the 1 MB limit.")
            lines = parse_lrc(path.read_text(encoding="utf-8-sig", errors="replace"))
            self.signals.finished.emit(str(self.path), lines, "" if lines else "No timed lyrics found.")
        except (OSError, ValueError) as exc:
            self.signals.finished.emit(str(self.path), [], f"Lyrics unavailable: {exc}")


class LyricsService(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.path = ""
        self.lines: list[LyricLine] = []
        self.status = "Open a track for local synchronized lyrics."
        self.jobs: list[LyricsJob] = []

    def load(self, path: Path | None) -> None:
        self.path = str(path) if path else ""
        self.lines = []
        self.status = "Loading local lyrics…" if path else "Open a track for local synchronized lyrics."
        self.changed.emit()
        if path:
            job = LyricsJob(path)
            job.signals.finished.connect(self._finished)
            self.jobs.append(job)
            self.pool.start(job)

    @Slot(str, object, str)
    def _finished(self, path: str, lines, status: str) -> None:
        self.jobs.pop(0)
        if path == self.path:
            self.lines, self.status = lines, status
            self.changed.emit()

    def shutdown(self) -> None:
        self.pool.waitForDone()
