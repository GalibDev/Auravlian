"""Shared presentation state; widgets do not own engines or queues."""
from PySide6.QtCore import QObject, Signal

from auravlian.application.playback_service import PlaybackService


def timestamp(milliseconds: int) -> str:
    seconds = max(0, milliseconds // 1000)
    return f"{seconds // 60}:{seconds % 60:02}"


class PlayerViewModel(QObject):
    changed = Signal()
    error_raised = Signal(str)

    def __init__(self, service: PlaybackService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.service = service
        service.changed.connect(self.changed)
        service.error_raised.connect(self.error_raised)

    @property
    def title(self) -> str:
        track = self.service.queue.current
        return track.title if track else "Nothing playing"

    @property
    def subtitle(self) -> str:
        service = self.service
        if service.error_message:
            prefix = f"{service.state.capitalize()} · " if service.queue.current else ""
            return prefix + service.error_message
        if not service.queue.current:
            return "Open local audio files to start listening"
        count = len(service.queue.tracks)
        return f"{service.state.capitalize()} · {count} {'file' if count == 1 else 'files'} in queue"

    @property
    def time_label(self) -> str:
        return f"{timestamp(self.service.position)} / {timestamp(self.service.duration)}"

    @property
    def has_tracks(self) -> bool:
        return self.service.queue.current is not None

    @property
    def can_play(self) -> bool:
        return self.has_tracks and self.service.state not in ("loading", "buffering")
