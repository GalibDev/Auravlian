from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QToolButton, QVBoxLayout, QStyle,
)

from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class PlaybackBar(QFrame):
    """Persistent controls driven exclusively by the shared playback view model."""

    favorite_requested = Signal()

    def __init__(self, vm: PlayerViewModel) -> None:
        super().__init__()
        self.vm = vm
        self.setObjectName("playback")
        self.setFixedHeight(86)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setObjectName("playerProgress")
        self.seek.setSingleStep(1000)
        self.seek.setPageStep(5000)
        self.seek.setFixedHeight(12)
        self.seek.setAccessibleName("Playback position")
        self.seek.sliderReleased.connect(lambda: vm.service.seek(self.seek.value()))
        self.seek.valueChanged.connect(self._seek_keyboard)
        root.addWidget(self.seek)
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 4, 16, 8)
        root.addLayout(layout, 1)
        self.cover = QLabel("♫")
        self.cover.setObjectName("musicCover")
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setFixedSize(56, 56)
        self.cover_path = ""
        layout.addWidget(self.cover)
        info = QVBoxLayout()
        self.title = QLabel()
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setFixedWidth(170)
        self.caption = QLabel()
        self.caption.setTextFormat(Qt.TextFormat.PlainText)
        self.caption.setObjectName("subtitle")
        self.caption.setWordWrap(True)
        self.caption.setMaximumWidth(250)
        self.caption.setMaximumHeight(48)
        info.addWidget(self.title)
        info.addWidget(self.caption)
        layout.addLayout(info, 2)
        self.favorite = QToolButton()
        self.favorite.setText("♡")
        self.favorite.setObjectName("playerFavorite")
        self.favorite.setCheckable(True)
        self.favorite.setToolTip("Favorite current track")
        self.favorite.setAccessibleName("Favorite current track")
        self.favorite.clicked.connect(self.favorite_requested)
        layout.addWidget(self.favorite)
        middle = QVBoxLayout()
        buttons = QHBoxLayout()
        self.buttons: dict[str, QPushButton] = {}
        service = vm.service
        commands = (service.toggle_shuffle, service.previous, service.toggle_play,
                    service.next, service.cycle_repeat)
        for name, command in zip(("Shuffle", "Previous", "Play", "Next", "Repeat"), commands):
            button = QPushButton(name)
            button.setAccessibleName(name)
            button.clicked.connect(command)
            self.buttons[name] = button
            buttons.addWidget(button)
            button.setToolTip(name)
            button.setObjectName("transport")
            button.setFixedSize(38, 38)
        for name, icon in (("Previous", QStyle.StandardPixmap.SP_MediaSkipBackward),
                           ("Next", QStyle.StandardPixmap.SP_MediaSkipForward)):
            self.buttons[name].setIcon(self.style().standardIcon(icon))
            self.buttons[name].setText("")
            self.buttons[name].setFixedWidth(40)
        self.buttons["Play"].setObjectName("primary")
        self.buttons["Shuffle"].setText("⤨")
        self.buttons["Repeat"].setText("↻")
        buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttons["Shuffle"].setCheckable(True)
        self.stop = QToolButton()
        self.stop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop.setToolTip("Stop")
        self.stop.setAccessibleName("Stop playback")
        self.stop.clicked.connect(service.stop)
        buttons.addWidget(self.stop)
        middle.addLayout(buttons)
        layout.addLayout(middle, 4)
        self.time = QLabel()
        self.time.setObjectName("subtitle")
        layout.addWidget(self.time)
        self.mute = QToolButton()
        self.mute.setAccessibleName("Mute playback")
        self.mute.setCheckable(True)
        self.mute.clicked.connect(service.set_muted)
        layout.addWidget(self.mute)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setAccessibleName("Playback volume")
        self.volume.setMaximumWidth(100)
        self.volume.valueChanged.connect(service.set_volume)
        layout.addWidget(self.volume)
        vm.changed.connect(self.refresh)
        self.refresh()

    def _seek_keyboard(self, value: int) -> None:
        if not self.seek.isSliderDown():
            self.vm.service.seek(value)

    def refresh(self) -> None:
        vm, service = self.vm, self.vm.service
        self.title.setText(vm.title)
        self.title.setToolTip(vm.title)
        track = service.queue.current
        path = track.artwork_path if track else ""
        if path != self.cover_path:
            self.cover_path = path
            pixmap = QPixmap(path) if path else QPixmap()
            self.cover.clear()
            if pixmap.isNull():
                self.cover.setText("♫")
            else:
                self.cover.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))
        self.caption.setText(vm.subtitle if service.error_message else (track.artist if track else vm.subtitle))
        self.caption.setToolTip(vm.subtitle)
        self.buttons["Play"].setText("")
        self.buttons["Play"].setToolTip("Pause" if service.state == "playing" else "Play")
        self.buttons["Play"].setAccessibleName(self.buttons["Play"].toolTip())
        self.buttons["Play"].setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_MediaPause if service.state == "playing"
            else QStyle.StandardPixmap.SP_MediaPlay))
        self.buttons["Play"].setEnabled(vm.can_play)
        self.buttons["Previous"].setEnabled(vm.has_tracks and (
            service.queue.can_previous or (service.seekable and service.position > 3000)))
        self.buttons["Next"].setEnabled(service.queue.can_next)
        self.buttons["Shuffle"].setEnabled(vm.has_tracks)
        self.buttons["Shuffle"].setChecked(service.queue.shuffle)
        self.buttons["Repeat"].setEnabled(vm.has_tracks)
        self.buttons["Repeat"].setText("↻¹" if service.queue.repeat.value == "one" else "↻")
        self.buttons["Repeat"].setToolTip(f"Repeat: {service.queue.repeat.value}")
        self.buttons["Repeat"].setProperty("active", service.queue.repeat.value != "off")
        self.buttons["Repeat"].style().unpolish(self.buttons["Repeat"])
        self.buttons["Repeat"].style().polish(self.buttons["Repeat"])
        self.stop.setEnabled(vm.has_tracks and service.state not in ("stopped", "error"))
        self.seek.setEnabled(service.ready and service.seekable and service.duration > 0)
        if not self.seek.isSliderDown():
            with QSignalBlocker(self.seek):
                self.seek.setRange(0, max(0, service.duration))
                self.seek.setValue(service.position)
        self.time.setText(vm.time_label)
        self.volume.setEnabled(vm.has_tracks)
        self.mute.setEnabled(vm.has_tracks)
        with QSignalBlocker(self.volume), QSignalBlocker(self.mute):
            self.volume.setValue(service.volume)
            self.mute.setChecked(service.muted)
        self.mute.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted
                                                   if service.muted else QStyle.StandardPixmap.SP_MediaVolume))
        self.mute.setToolTip("Unmute" if service.muted else "Mute")

