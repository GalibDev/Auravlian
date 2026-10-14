from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QToolButton, QVBoxLayout,
)

from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class PlaybackBar(QFrame):
    """Persistent controls driven exclusively by the shared playback view model."""

    def __init__(self, vm: PlayerViewModel) -> None:
        super().__init__()
        self.vm = vm
        self.setObjectName("playback")
        self.setMinimumHeight(108)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        info = QVBoxLayout()
        self.title = QLabel()
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setMaximumWidth(250)
        self.caption = QLabel()
        self.caption.setTextFormat(Qt.TextFormat.PlainText)
        self.caption.setObjectName("subtitle")
        self.caption.setWordWrap(True)
        self.caption.setMaximumWidth(250)
        self.caption.setMaximumHeight(48)
        info.addWidget(self.title)
        info.addWidget(self.caption)
        layout.addLayout(info, 2)
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
        self.buttons["Shuffle"].setCheckable(True)
        self.stop = QToolButton()
        self.stop.setText("Stop")
        self.stop.setAccessibleName("Stop playback")
        self.stop.clicked.connect(service.stop)
        buttons.addWidget(self.stop)
        middle.addLayout(buttons)
        timeline = QHBoxLayout()
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setSingleStep(1000)
        self.seek.setPageStep(5000)
        self.seek.setAccessibleName("Playback position")
        self.seek.sliderReleased.connect(lambda: service.seek(self.seek.value()))
        self.seek.valueChanged.connect(self._seek_keyboard)
        self.time = QLabel()
        timeline.addWidget(self.seek, 1)
        timeline.addWidget(self.time)
        middle.addLayout(timeline)
        layout.addLayout(middle, 4)
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
        self.caption.setText(vm.subtitle)
        self.caption.setToolTip(vm.subtitle)
        self.buttons["Play"].setText("Pause" if service.state == "playing" else "Play")
        self.buttons["Play"].setEnabled(vm.can_play)
        self.buttons["Previous"].setEnabled(vm.has_tracks and (
            service.queue.can_previous or (service.seekable and service.position > 3000)))
        self.buttons["Next"].setEnabled(service.queue.can_next)
        self.buttons["Shuffle"].setEnabled(vm.has_tracks)
        self.buttons["Shuffle"].setChecked(service.queue.shuffle)
        self.buttons["Repeat"].setEnabled(vm.has_tracks)
        self.buttons["Repeat"].setText(f"Repeat: {service.queue.repeat.value}")
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
        self.mute.setText("Unmute" if service.muted else "Mute")

