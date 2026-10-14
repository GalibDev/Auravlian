from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from auravlian.shared.paths import asset_path

PAGES = ("Home", "Library", "Albums", "Artists", "Playlists", "Favorites",
         "Recently Played", "Now Playing", "Settings")


class Sidebar(QFrame):
    selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(246)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 20)
        branding = QHBoxLayout()
        logo = QLabel()
        # Crop only the old wordmark; the source symbol pixels are unchanged.
        symbol = QPixmap(str(asset_path("logo", "original.png"))).copy(0, 0, 1254, 830)
        logo.setPixmap(symbol.scaled(44, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        branding.addWidget(logo)
        brand = QLabel("Auravlian")
        brand.setObjectName("brand")
        branding.addWidget(brand)
        branding.addStretch()
        layout.addLayout(branding)
        tagline = QLabel("Feel Beyond Sound.")
        tagline.setObjectName("subtitle")
        layout.addWidget(tagline)
        layout.addSpacing(24)
        label = QLabel("YOUR SPACE")
        label.setObjectName("eyebrow")
        layout.addWidget(label)
        self.group = QButtonGroup(self)
        self.buttons: dict[str, QPushButton] = {}
        for page in PAGES:
            button = QPushButton(page)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setAccessibleName(f"Navigate to {page}")
            button.clicked.connect(lambda checked=False, name=page: self.selected.emit(name))
            self.group.addButton(button)
            self.buttons[page] = button
            layout.addWidget(button)
        layout.addStretch()
        status = QLabel("OFFLINE FIRST  /  v0.8.0")
        status.setObjectName("eyebrow")
        layout.addWidget(status)

