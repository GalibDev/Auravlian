from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from auravlian.presentation.pages.base import label


class HomePage(QWidget):
    open_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(label("Welcome home", "section"))
        heading.addWidget(label("Your music, your universe", "subtitle"))
        header.addLayout(heading, 1)
        search = QLineEdit()
        search.setPlaceholderText("Search tracks, albums… · Phase 3")
        search.setAccessibleName("Library search — available in Phase 3")
        search.setEnabled(False)
        search.setMaximumWidth(284)
        header.addWidget(search)
        layout.addLayout(header)
        hero = QFrame()
        hero.setObjectName("hero")
        content = QVBoxLayout(hero)
        content.setContentsMargins(30, 30, 30, 30)
        content.addWidget(label("WELCOME TO AURAVLIAN", "eyebrow"))
        content.addWidget(label("Feel every beat.", "title"))
        content.addWidget(label(
            "Your personal music universe. Entirely offline.", "subtitle"))
        button = QPushButton("Open audio files…")
        button.setObjectName("primary")
        button.clicked.connect(self.open_requested)
        content.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hero)
        layout.addWidget(label("Recently Added", "section"))
        cards = QHBoxLayout()
        for title, detail in (
            ("Your albums", "No albums imported"),
            ("Your artists", "No artists imported"),
            ("Your favorites", "No favorites yet"),
            ("Your playlists", "No playlists yet"),
        ):
            card = QFrame()
            card.setObjectName("card")
            body = QVBoxLayout(card)
            body.setContentsMargins(20, 24, 20, 24)
            placeholder = QFrame()
            placeholder.setObjectName("artworkPlaceholder")
            placeholder.setMinimumHeight(120)
            body.addWidget(placeholder)
            body.addWidget(label(title, "section"))
            body.addWidget(label(detail, "subtitle"))
            cards.addWidget(card)
        layout.addLayout(cards)
        layout.addWidget(label("Recently Played", "section"))
        recent = QFrame()
        recent.setObjectName("card")
        recent_body = QVBoxLayout(recent)
        recent_body.setContentsMargins(18, 16, 18, 16)
        recent_body.addWidget(label("Your listening history will appear here after your first play.",
                                    "subtitle"))
        layout.addWidget(recent)
        layout.addStretch()
        layout.addWidget(label("LOCAL PLAYBACK  ·  Library import arrives in Phase 3.",
                               "subtitle"))

