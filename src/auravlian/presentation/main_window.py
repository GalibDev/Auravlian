from PySide6.QtCore import QByteArray, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QMainWindow, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
    QApplication, QSystemTrayIcon, QMenu,
)
from PySide6.QtGui import QShortcut
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.presentation.widgets.queue_panel import QueuePanel
from auravlian.presentation.widgets.mini_player import MiniPlayer

from auravlian.app.container import Container
from auravlian.presentation.pages.collections import CollectionPage
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
        self.force_quit = False
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
        home = HomePage(container.library, container.collections)
        home.open_requested.connect(self.open_files)
        home.library_requested.connect(lambda: self.navigate("Library"))
        home.collection_requested.connect(self.navigate)
        self.pages: dict[str, QWidget] = {"Home": home}
        for name in ("Albums", "Artists", "Playlists", "Favorites", "Recently Played"):
            self.pages[name] = CollectionPage(name, container.collections)
        engine = self.player_vm.service.audio
        self.pages["Settings"] = SettingsPage(container.settings, engine if isinstance(engine, QtAudioEngine) else None)
        self.pages["Library"] = LibraryPage(container.library, container.collections)
        now_playing = NowPlayingPage(self.player_vm)
        now_playing.open_requested.connect(self.open_files)
        now_playing.fullscreen_requested.connect(self.toggle_fullscreen)
        now_playing.mini_requested.connect(self.show_mini)
        now_playing.queue_requested.connect(self.show_queue)
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
        self.queue_panel = QueuePanel(self.player_vm, self)
        self.mini_player = MiniPlayer(self.player_vm, self)
        view_menu = self.menuBar().addMenu("View")
        for name, action in (("Playback queue", self.show_queue), ("Mini-player", self.show_mini),
                             ("Fullscreen Now Playing", self.toggle_fullscreen)):
            item = QAction(name, self)
            item.triggered.connect(action)
            view_menu.addAction(item)
        for key, action in (("Ctrl+Space", self.player_vm.service.toggle_play),
                            ("Ctrl+Right", self.player_vm.service.next),
                            ("Ctrl+Left", self.player_vm.service.previous),
                            ("Ctrl+M", lambda: self.player_vm.service.set_muted(not self.player_vm.service.muted)),
                            ("Ctrl+Shift+M", self.show_mini), ("F11", self.toggle_fullscreen),
                            ("Escape", self.exit_fullscreen)):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(action)
        self.tray = QSystemTrayIcon(QApplication.windowIcon(), self)
        self.tray.setToolTip("Auravlian — Feel Beyond Sound.")
        tray_menu = QMenu(self)
        for name, action in (("Show Auravlian", self.restore_window), ("Mini-player", self.show_mini),
                             ("Play / Pause", self.player_vm.service.toggle_play),
                             ("Next", self.player_vm.service.next), ("Quit", self.quit_application)):
            item = tray_menu.addAction(name)
            item.triggered.connect(action)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda reason: self.restore_window()
                                    if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.sidebar.selected.connect(self.navigate)
        settings = container.settings
        geometry = settings.value("window/geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        page = str(settings.value("window/page", "Home")) if settings.value(
            "startup/remember_page", True, type=bool) else "Home"
        self.navigate(page if page in PAGES else "Home")

    def show_queue(self) -> None:
        self.queue_panel.show()
        self.queue_panel.raise_()

    def show_mini(self) -> None:
        self.mini_player.show()
        self.mini_player.raise_()

    def restore_window(self) -> None:
        self.showNormal()
        self.sidebar.show()
        self.menuBar().show()
        self.raise_()
        self.activateWindow()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.navigate("Now Playing")
            self.sidebar.hide()
            self.menuBar().hide()
            self.showFullScreen()

    def exit_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.sidebar.show()
            self.menuBar().show()

    def quit_application(self) -> None:
        self.force_quit = True
        self.close()

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
        if (not self.force_quit and self.tray.isVisible()
                and self.container.settings.value("desktop/tray", False, type=bool)):
            self.hide()
            event.ignore()
            return
        self.player_vm.service.stop()
        self.container.settings.setValue("window/geometry", self.saveGeometry())
        self.container.settings.sync()
        if self.container.library.service.busy or self.container.collections.service.busy:
            self.container.library.service.cancel()
            event.ignore()
            QTimer.singleShot(50, self.close)
            return
        super().closeEvent(event)
        self.tray.hide()
        self.mini_player.close()
        self.queue_panel.close()
        if self.force_quit:
            QTimer.singleShot(0, QApplication.quit)

