from pathlib import Path

from PySide6.QtCore import QObject, Signal

from auravlian.application.library_service import LibraryService
from auravlian.application.playback_service import PlaybackService
from auravlian.domain.models.track import Track


class LibraryViewModel(QObject):
    changed = Signal()

    def __init__(self, service: LibraryService, playback: PlaybackService,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.service, self.playback = service, playback
        service.changed.connect(self.changed)
        service.progress.connect(lambda _: self.changed.emit())

    def import_paths(self, paths: list[Path]) -> None:
        self.service.start("import", paths)

    def play(self, tracks: list[Track]) -> None:
        available = [track for track in tracks if not track.missing]
        if available:
            self.playback.open_tracks(available)
