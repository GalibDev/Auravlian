from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.library_vm import LibraryViewModel


class HomePage(QWidget):
    open_requested = Signal()
    library_requested = Signal()

    def __init__(self, library: LibraryViewModel | None = None) -> None:
        super().__init__()
        self.library_vm = library
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(label("Welcome home", "section"))
        heading.addWidget(label("Your music, your universe", "subtitle"))
        header.addLayout(heading, 1)
        search = QLineEdit()
        search.setPlaceholderText("Search from Music Library")
        search.setAccessibleName("Use the Music Library page to search")
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
        browse = QPushButton("Browse music library")
        browse.clicked.connect(self.library_requested)
        content.addWidget(browse, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hero)
        layout.addWidget(label("Recently Added", "section"))
        cards = QHBoxLayout()
        self.collection_labels = []
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
            detail_label = label(detail, "subtitle")
            body.addWidget(detail_label)
            self.collection_labels.append(detail_label)
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
        layout.addWidget(label("LOCAL MUSIC  ·  Import, search and play from Music Library.",
                               "subtitle"))
        if library is not None:
            library.changed.connect(self.refresh_library)
            self.refresh_library()

    def refresh_library(self) -> None:
        if self.library_vm is None:
            return
        tracks = self.library_vm.service.tracks
        self.collection_labels[0].setText(f"{len({(t.album, t.artist) for t in tracks})} imported albums")
        self.collection_labels[1].setText(f"{len({t.artist for t in tracks})} imported artists")

