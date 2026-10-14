from PySide6.QtCore import QObject, Signal, Slot

from auravlian.application.playlist_service import PlaylistService
from auravlian.domain.models.track import Track
from auravlian.presentation.viewmodels.library_vm import LibraryViewModel


class CollectionViewModel(QObject):
    changed = Signal()

    def __init__(self, service: PlaylistService, library: LibraryViewModel,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.service, self.library = service, library
        service.changed.connect(self.changed)
        library.changed.connect(self._library_changed)

    @Slot()
    def _library_changed(self) -> None:
        if not self.library.service.busy:
            self.service.refresh()
        self.changed.emit()

    def play(self, tracks: list[Track]) -> None:
        self.library.play(tracks)

    def groups(self, kind: str) -> dict[str, list[Track]]:
        groups: dict[str, list[Track]] = {}
        for track in self.library.service.tracks:
            key = f"{track.album} — {track.artist}" if kind == "Albums" else track.artist
            groups.setdefault(key, []).append(track)
        return dict(sorted(groups.items(), key=lambda pair: pair[0].casefold()))
