"""Compact favorite track presentation without changing library columns."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from auravlian.presentation.viewmodels.player_vm import timestamp
from auravlian.presentation.widgets.track_table import TrackTableModel, artwork_icon


class FavoriteTableModel(TrackTableModel):
    HEADERS = ("♥", "Artist", "Title", "Duration")

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.tracks):
            return None
        track = self.tracks[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return ("♥", track.artist, track.title, timestamp(track.duration_ms))[index.column()]
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 1 and track.artwork_path:
            return artwork_icon(track.artwork_path)
        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 0:
            return QColor("#E74783")
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{'Missing file: ' if track.missing else ''}{track.path}"
        return None
