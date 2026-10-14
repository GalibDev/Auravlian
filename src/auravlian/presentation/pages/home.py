from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from auravlian.domain.models.track import Track
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.library_vm import LibraryViewModel
from auravlian.presentation.viewmodels.playlist_vm import CollectionViewModel


class HomePage(QWidget):
    open_requested = Signal()
    library_requested = Signal()
    collection_requested = Signal(str)

    def __init__(self, library: LibraryViewModel | None = None,
                 collections: CollectionViewModel | None = None) -> None:
        super().__init__()
        self.library_vm = library
        self.collection_vm = collections
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
        layout.addWidget(label("Your Collections", "section"))
        cards = QHBoxLayout()
        self.collection_labels = []
        self.cards: dict[str, QPushButton] = {}
        self.artworks: dict[str, QPushButton] = {}
        for page, title, detail in (
            ("Albums", "Your albums", "No albums imported"),
            ("Artists", "Your artists", "No artists imported"),
            ("Favorites", "Your favorites", "No favorites yet"),
            ("Playlists", "Your playlists", "No playlists yet"),
        ):
            card = QPushButton()
            card.setObjectName("card")
            card.setAccessibleName(f"Browse {page}")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.clicked.connect(lambda checked=False, name=page: self.collection_requested.emit(name))
            self.cards[page] = card
            body = QVBoxLayout(card)
            body.setContentsMargins(20, 24, 20, 24)
            placeholder = QPushButton("♪\nBrowse " + page)
            placeholder.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            placeholder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            placeholder.setObjectName("artworkPlaceholder")
            placeholder.setMinimumHeight(120)
            self.artworks[page] = placeholder
            body.addWidget(placeholder)
            body.addWidget(label(title, "section"))
            detail_label = label(detail, "subtitle")
            body.addWidget(detail_label)
            self.collection_labels.append(detail_label)
            for child in (body.itemAt(1).widget(), detail_label):
                if child is not None:
                    child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            cards.addWidget(card)
        layout.addLayout(cards)
        layout.addWidget(label("Recently Played", "section"))
        recent = QFrame()
        recent.setObjectName("card")
        recent_body = QVBoxLayout(recent)
        recent_body.setContentsMargins(18, 16, 18, 16)
        self.recent_history = label("Your listening history will appear here after your first play.", "subtitle")
        recent_body.addWidget(self.recent_history)
        layout.addWidget(recent)
        layout.addStretch()
        layout.addWidget(label("LOCAL MUSIC  ·  Import, search and play from Music Library.",
                               "subtitle"))
        if library is not None:
            library.changed.connect(self.refresh_library)
            self.refresh_library()
        if collections is not None:
            collections.changed.connect(self.refresh_collections)
            self.refresh_collections()

    def refresh_collections(self) -> None:
        if self.collection_vm is None:
            return
        snapshot = self.collection_vm.service.snapshot
        self.set_artwork("Favorites", snapshot.favorites)
        self.set_artwork("Playlists", [track for playlist in snapshot.playlists for track in playlist.tracks])
        self.collection_labels[2].setText(f"{len(snapshot.favorites)} favorites")
        self.collection_labels[3].setText(f"{len(snapshot.playlists)} playlists")
        self.recent_history.setText("  ·  ".join(track.title for track in snapshot.history[:3]) or
                                   "Your listening history will appear here after your first play.")

    def refresh_library(self) -> None:
        if self.library_vm is None:
            return
        tracks = self.library_vm.service.tracks
        self.set_artwork("Albums", tracks)
        self.set_artwork("Artists", tracks)
        self.collection_labels[0].setText(f"{len({(t.album, t.artist) for t in tracks})} imported albums")
        self.collection_labels[1].setText(f"{len({t.artist for t in tracks})} imported artists")

    def set_artwork(self, page: str, tracks: list[Track]) -> None:
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize

        preview = self.artworks[page]
        preview.setIcon(QIcon())
        preview.setText("♪\nBrowse " + page if tracks else "♪\nNo music yet")
        for track in tracks:
            pixmap = QPixmap(track.artwork_path) if track.artwork_path else QPixmap()
            if not pixmap.isNull():
                preview.setIcon(QIcon(pixmap))
                preview.setIconSize(QSize(160, 120))
                preview.setText("")
                break

