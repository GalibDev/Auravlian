"""Artwork-first, keyboard accessible local music tile."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from auravlian.domain.models.track import Track


class MusicCard(QPushButton):
    def __init__(self, track: Track) -> None:
        super().__init__()
        self.setObjectName("musicCard")
        self.setFixedSize(172, 202)
        self.setText(f"{track.title[:23]}\n{track.artist[:25]}")
        self.setToolTip(f"Play {track.title} — {track.artist}")
        self.setAccessibleName(f"Play {track.title} by {track.artist}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        icon = QIcon(track.artwork_path) if track.artwork_path else QIcon()
        # A cover is optional; a music glyph remains useful without metadata.
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        layout = QVBoxLayout(self)
        cover = QLabel("♫")
        cover.setObjectName("musicCover")
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setFixedSize(146, 140)
        if not icon.isNull():
            cover.setPixmap(icon.pixmap(QSize(146, 140)))
        layout.addWidget(cover)
        title = QLabel(track.title)
        title.setMaximumWidth(146)
        title.setToolTip(track.title)
        artist = QLabel(track.artist)
        artist.setObjectName("subtitle")
        artist.setMaximumWidth(146)
        layout.addWidget(title)
        layout.addWidget(artist)
        self.setText("")
        for child in (cover, title, artist):
            child.setTextFormat(Qt.TextFormat.PlainText)
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setEnabled(not track.missing)
