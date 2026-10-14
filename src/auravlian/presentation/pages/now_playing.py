from PySide6.QtCore import Signal, QCoreApplication, Qt
from pathlib import Path
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QLabel

from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel
from auravlian.application.lyrics_service import LyricsService
from auravlian.domain.playback.lyrics import current_line
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.presentation.widgets.spectrum import SpectrumWidget


class NowPlayingPage(QWidget):
    open_requested = Signal()
    fullscreen_requested = Signal()
    mini_requested = Signal()
    queue_requested = Signal()

    def __init__(self, vm: PlayerViewModel) -> None:
        super().__init__()
        self.vm = vm
        self.current_path: Path | None = None
        self.lyrics = LyricsService(QCoreApplication.instance())
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.lyrics.shutdown)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(10)
        layout.addWidget(label("GIVE THE MUSIC YOUR FULL ATTENTION", "eyebrow"))
        layout.addWidget(label("Now Playing", "title"))
        card = QFrame()
        card.setObjectName("hero")
        body = QHBoxLayout(card)
        body.setContentsMargins(24, 20, 24, 20)
        self.artwork = QLabel("No embedded artwork")
        self.artwork.setFixedSize(192, 192)
        self.artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self.artwork)
        details = QVBoxLayout()
        body.addLayout(details, 1)
        self.track = label("", "title")
        self.status = label("", "subtitle")
        self.time = label("", "section")
        details.addWidget(self.track)
        details.addWidget(self.status)
        details.addWidget(self.time)
        open_button = QPushButton("Open audio files…")
        open_button.setObjectName("primary")
        open_button.setToolTip("Open files replaces the current session queue.")
        open_button.clicked.connect(self.open_requested)
        details.addWidget(open_button)
        layout.addWidget(card)
        tools = QHBoxLayout()
        for name, signal in (("Fullscreen", self.fullscreen_requested), ("Mini-player", self.mini_requested),
                             ("Playback queue", self.queue_requested)):
            button = QPushButton(name)
            button.clicked.connect(signal)
            tools.addWidget(button)
        layout.addLayout(tools)
        self.spectrum = SpectrumWidget()
        engine = vm.service.audio
        if isinstance(engine, QtAudioEngine):
            engine.spectrum.changed.connect(self.spectrum.set_values)
        layout.addWidget(self.spectrum)
        self.lyric_status = label("", "subtitle")
        layout.addWidget(self.lyric_status)
        self.lyric_list = QListWidget()
        self.lyric_list.setMinimumHeight(140)
        self.lyric_list.setAccessibleName("Synchronized local lyrics")
        layout.addWidget(self.lyric_list)
        self.lyrics.changed.connect(self.render_lyrics)
        vm.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.track.setText(self.vm.title)
        self.status.setText(self.vm.subtitle)
        self.time.setText(self.vm.time_label)
        track = self.vm.service.queue.current
        path = track.path if track else None
        if path != self.current_path:
            self.current_path = path
            self.lyrics.load(path)
            self.artwork.clear()
            image = QPixmap(track.artwork_path) if track and track.artwork_path else QPixmap()
            if not image.isNull():
                self.artwork.setPixmap(image.scaled(192, 192, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
                accent = QColor(image.toImage().scaled(1, 1).pixel(0, 0))
                self.artwork.setStyleSheet(f"border: 2px solid {accent.name()}; border-radius: 12px;")
            else:
                self.artwork.setText("No embedded artwork")
                self.artwork.setStyleSheet("")
        index = current_line(self.lyrics.lines, self.vm.service.position)
        if index >= 0 and self.lyric_list.currentRow() != index:
            self.lyric_list.setCurrentRow(index)
            self.lyric_list.scrollToItem(self.lyric_list.item(index))

    def render_lyrics(self) -> None:
        self.lyric_status.setText(self.lyrics.status)
        self.lyric_list.clear()
        self.lyric_list.addItems([line.text for line in self.lyrics.lines])
        self.refresh()
