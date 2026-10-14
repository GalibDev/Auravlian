from functools import lru_cache

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtGui import QIcon

from auravlian.domain.models.track import Track
from auravlian.presentation.viewmodels.player_vm import timestamp
from auravlian.application.search_service import matches


@lru_cache(maxsize=128)
def artwork_icon(path: str) -> QIcon:
    return QIcon(path)


class TrackTableModel(QAbstractTableModel):
    HEADERS = ("Title", "Artist", "Album", "Duration", "Status")

    def __init__(self) -> None:
        super().__init__()
        self.tracks: list[Track] = []

    def replace(self, tracks: list[Track]) -> None:
        if tracks is self.tracks:
            return
        self.beginResetModel()
        self.tracks = tracks
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.tracks)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index: QModelIndex | QPersistentModelIndex,
             role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.tracks):
            return None
        track = self.tracks[index.row()]
        values = (track.title, track.artist, track.album, timestamp(track.duration_ms),
                  "Missing" if track.missing else "Available")
        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.UserRole:
            return track.duration_ms if index.column() == 3 else values[index.column()].casefold()
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(track.path)
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0 and track.artwork_path:
            return artwork_icon(track.artwork_path)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None


class TrackFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.query = ""

    def search(self, query: str) -> None:
        self.query = query
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int,
                         source_parent: QModelIndex | QPersistentModelIndex) -> bool:
        model = self.sourceModel()
        return isinstance(model, TrackTableModel) and matches(model.tracks[source_row], self.query)
