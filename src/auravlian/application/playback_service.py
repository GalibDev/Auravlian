"""Playback orchestration; engine signals are wired at the composition root."""
import json
import logging
import os
from pathlib import Path
from collections.abc import Iterable

from PySide6.QtCore import QObject, QTimer, Signal

from auravlian.domain.interfaces.audio_port import AudioPort
from auravlian.domain.models.track import Track
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.domain.playback.repeat_mode import RepeatMode


class PlaybackService(QObject):
    changed = Signal()
    error_raised = Signal(str)

    def __init__(self, audio: AudioPort, queue: PlaybackQueue,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.audio = audio
        self.queue = queue
        self.state = "empty"
        self.position = 0
        self.duration = 0
        self.ready = False
        self.seekable = False
        self.volume = 70
        self.muted = False
        self.error_message = ""
        self._generation = 0
        self._failed: set[Path] = set()
        self._failure_pending = False
        self._closed = False

    def open_files(self, paths: Iterable[str | Path]) -> None:
        tracks: list[Track] = []
        seen: set[str] = set()
        rejected: list[str] = []
        for value in paths:
            try:
                path = Path(value).expanduser().resolve()
                if not path.is_file():
                    rejected.append(f"File not found: {path.name}")
                    continue
                key = os.path.normcase(str(path))
                if key not in seen:
                    seen.add(key)
                    tracks.append(Track(path))
            except (OSError, ValueError) as exc:
                rejected.append(f"Cannot open file: {exc}")
        if not tracks:
            if rejected:
                self._report("; ".join(rejected))
            return
        self._failed.clear()
        self.queue.replace(tracks)
        self._load_current()
        if rejected:
            self._report("; ".join(rejected))

    def _load_current(self) -> None:
        track = self.queue.current
        if track is None or self._closed:
            return
        self._generation += 1
        self._failure_pending = False
        self.state = "loading"
        self.ready = self.seekable = False
        self.position = self.duration = 0
        self.error_message = ""
        self.changed.emit()
        try:
            exists = track.path.is_file()
        except OSError as exc:
            self.on_error(f"Cannot access {track.path.name}: {exc}")
            return
        if not exists:
            self.on_error(f"File no longer exists: {track.path.name}")
            return
        self.audio.load(track.path)

    def open_tracks(self, tracks: Iterable[Track]) -> None:
        """Play repository snapshots without discarding their metadata."""
        selected = list(tracks)
        if selected:
            self._failed.clear()
            self.queue.replace(selected)
            self._load_current()

    def play(self) -> None:
        if self.queue.current is None:
            return
        if self.state == "error":
            self._failed.clear()
            self._load_current()
        elif self.state not in ("loading", "buffering"):
            self.audio.play()

    def pause(self) -> None:
        if self.state == "playing":
            self.audio.pause()

    def toggle_play(self) -> None:
        self.pause() if self.state == "playing" else self.play()

    def stop(self) -> None:
        self._generation += 1
        self._failure_pending = False
        self.audio.stop()
        self.state = "stopped" if self.queue.current else "empty"
        self.position = 0
        self.changed.emit()

    def next(self) -> None:
        if self.queue.next() is not None:
            self._failed.clear()
            self._load_current()

    def previous(self) -> None:
        if self.position > 3000 and self.seekable:
            self.seek(0)
        elif self.queue.previous() is not None:
            self._failed.clear()
            self._load_current()

    def seek(self, milliseconds: int) -> None:
        if self.ready and self.seekable:
            self.audio.seek(max(0, min(milliseconds, self.duration)))

    def set_volume(self, percent: int) -> None:
        self.volume = max(0, min(percent, 100))
        self.audio.set_volume(self.volume)
        self.changed.emit()

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        self.audio.set_muted(muted)
        self.changed.emit()

    def toggle_shuffle(self) -> None:
        self.queue.set_shuffle(not self.queue.shuffle)
        self.changed.emit()

    def cycle_repeat(self) -> None:
        modes = list(RepeatMode)
        self.queue.repeat = modes[(modes.index(self.queue.repeat) + 1) % len(modes)]
        self.changed.emit()

    def on_state(self, state: str) -> None:
        if self.state != "error" and not self._closed:
            self.state = state if self.queue.current else "empty"
            self.changed.emit()

    def on_position(self, milliseconds: int) -> None:
        self.position = milliseconds
        self.changed.emit()

    def on_duration(self, milliseconds: int) -> None:
        self.duration = milliseconds
        self.changed.emit()

    def on_ready(self, ready: bool) -> None:
        self.ready = ready and self.state != "error"
        self.changed.emit()

    def on_seekable(self, seekable: bool) -> None:
        self.seekable = seekable
        self.changed.emit()

    def on_ended(self) -> None:
        generation = self._generation
        QTimer.singleShot(0, lambda: self._complete(generation))

    def _complete(self, generation: int) -> None:
        if self._closed or generation != self._generation or self.state == "error":
            return
        # Invalidate duplicate completion callbacks, including repeat-one cycles.
        self._generation += 1
        if self.queue.next(completed=True) is not None:
            self._failed.clear()
            self._load_current()
        else:
            self.state = "stopped"
            self.changed.emit()

    def _report(self, message: str) -> None:
        self.error_message = message
        logging.getLogger("auravlian").warning(json.dumps(message))
        self.error_raised.emit(message)
        self.changed.emit()

    def on_error(self, message: str) -> None:
        if self._closed or self._failure_pending:
            return
        self.state = "error"
        self.ready = False
        self.seekable = False
        self._report(message)
        track = self.queue.current
        if track is None or message.startswith(("No audio output", "Audio output disconnected")):
            return
        self._failed.add(track.path)
        self._failure_pending = True
        generation = self._generation
        QTimer.singleShot(0, lambda: self._recover(generation))

    def _recover(self, generation: int) -> None:
        if self._closed or generation != self._generation:
            return
        self._failure_pending = False
        # Explicit next ignores repeat-one. Failed paths cannot loop under repeat-all.
        for _ in self.queue.tracks:
            track = self.queue.next()
            if track is None:
                break
            if track.path not in self._failed:
                previous_error = self.error_message
                self._load_current()
                if not self.error_message:
                    self.error_message = previous_error
                    self.changed.emit()
                return
        self.audio.stop()
        self.state = "error"
        self.changed.emit()

    def shutdown(self) -> None:
        if not self._closed:
            self._closed = True
            self._generation += 1
            self.audio.stop()
