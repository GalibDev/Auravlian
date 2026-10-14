from PySide6.QtCore import QByteArray, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QMainWindow, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from auravlian.app.container import Container
from auravlian.presentation.pages.base import EmptyPage
from auravlian.presentation.pages.home import HomePage
from auravlian.presentation.pages.library import LibraryPage
from auravlian.presentation.pages.now_playing import NowPlayingPage
from auravlian.presentation.pages.settings import SettingsPage
from auravlian.presentation.widgets.playback_bar import PlaybackBar
from auravlian.presentation.widgets.sidebar import PAGES, Sidebar


class MainWindow(QMainWindow):
    def __init__(self, container: Container) -> None:
        super().__init__()
        self.container = container
        self.setWindowTitle("Auravlian — Feel Beyond Sound.")
        self.resize(1440, 900)
        self.setMinimumSize(960, 700)
        root = QWidget()
        vertical = QVBoxLayout(root)
        vertical.setContentsMargins(0, 0, 0, 0)
        vertical.setSpacing(0)
        top = QHBoxLayout()
        top.setSpacing(0)
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        self.player_vm = container.player
        home = HomePage(container.library)
        home.open_requested.connect(self.open_files)
        home.library_requested.connect(lambda: self.navigate("Library"))
        self.pages: dict[str, QWidget] = {"Home": home}
        definitions = {
            "Albums": ("Every record has a story.", "No albums yet",
                       "Albums will be grouped from your local music metadata.", 4),
            "Artists": ("The voices behind your collection.", "No artists yet",
                        "Discover artists from your imported library in Phase 4.", 4),
            "Playlists": ("A soundtrack for every moment.", "Create your own flow",
                          "Playlist creation and editing arrive in Phase 4.", 4),
            "Favorites": ("Keep the songs that stay with you.", "Nothing favorited yet",
                          "Mark favorites from your library in Phase 4.", 4),
            "Recently Played": ("Find your way back to a feeling.", "Your history begins with a play",
                                "Listening history arrives in Phase 4.", 4),
        }
        for name, (subtitle, empty, detail, phase) in definitions.items():
            self.pages[name] = EmptyPage(name, subtitle, empty, detail, phase)
        self.pages["Settings"] = SettingsPage(container.settings)
        self.pages["Library"] = LibraryPage(container.library)
        now_playing = NowPlayingPage(self.player_vm)
        now_playing.open_requested.connect(self.open_files)
        self.pages["Now Playing"] = now_playing
        for name in PAGES:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(self.pages[name])
            self.stack.addWidget(scroll)
        top.addWidget(self.sidebar)
        top.addWidget(self.stack, 1)
        vertical.addLayout(top, 1)
        self.playback_bar = PlaybackBar(self.player_vm)
        vertical.addWidget(self.playback_bar)
        self.setCentralWidget(root)
        menu = self.menuBar().addMenu("File")
        open_action = QAction("Open audio files…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_files)
        menu.addAction(open_action)
        self.sidebar.selected.connect(self.navigate)
        settings = container.settings
        geometry = settings.value("window/geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        page = str(settings.value("window/page", "Home")) if settings.value(
            "startup/remember_page", True, type=bool) else "Home"
        self.navigate(page if page in PAGES else "Home")

    def open_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open local audio files", "",
            "Audio files (*.mp3 *.flac *.wav *.ogg *.m4a *.aac *.wma *.opus *.aiff);;All files (*)")
        if paths:
            self.player_vm.service.open_files(paths)

    def navigate(self, name: str) -> None:
        if name not in PAGES:
            return
        self.stack.setCurrentIndex(PAGES.index(name))
        self.sidebar.buttons[name].setChecked(True)
        self.container.settings.setValue("window/page", name)
        self.container.events.page_changed.emit(name)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.player_vm.service.stop()
        self.container.settings.setValue("window/geometry", self.saveGeometry())
        self.container.settings.sync()
        if self.container.library.service.busy:
            self.container.library.service.cancel()
            event.ignore()
            QTimer.singleShot(50, self.close)
            return
        super().closeEvent(event)

