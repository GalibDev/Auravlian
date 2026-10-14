from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QCheckBox
from PySide6.QtCore import Qt, QSignalBlocker

from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class MiniPlayer(QDialog):
    def __init__(self, vm: PlayerViewModel, parent=None) -> None:
        super().__init__(parent)
        self.vm = vm
        self.setWindowTitle("Auravlian — Mini-player")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.resize(480, 240)
        layout = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.buttons: dict[str, QPushButton] = {}
        service = vm.service
        for name, action in (("Previous", service.previous), ("Play", service.toggle_play),
                             ("Next", service.next), ("Stop", service.stop)):
            button = QPushButton(name)
            button.clicked.connect(action)
            self.buttons[name] = button
            actions.addWidget(button)
        layout.addLayout(actions)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setAccessibleName("Mini-player playback position")
        self.seek.sliderReleased.connect(lambda: service.seek(self.seek.value()))
        layout.addWidget(self.seek)
        bottom = QHBoxLayout()
        self.time = QLabel()
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setAccessibleName("Mini-player volume")
        self.volume.valueChanged.connect(service.set_volume)
        self.mute = QCheckBox("Mute")
        self.mute.toggled.connect(service.set_muted)
        bottom.addWidget(self.time)
        bottom.addWidget(self.volume)
        bottom.addWidget(self.mute)
        layout.addLayout(bottom)
        vm.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        service = self.vm.service
        self.title.setText(self.vm.title)
        self.status.setText(self.vm.subtitle)
        self.buttons["Play"].setText("Pause" if service.state == "playing" else "Play")
        self.buttons["Play"].setEnabled(self.vm.can_play)
        self.buttons["Next"].setEnabled(service.queue.can_next)
        self.buttons["Previous"].setEnabled(service.queue.can_previous or service.position > 3000)
        self.buttons["Stop"].setEnabled(self.vm.has_tracks)
        self.seek.setEnabled(service.ready and service.seekable)
        if not self.seek.isSliderDown():
            with QSignalBlocker(self.seek):
                self.seek.setRange(0, service.duration)
                self.seek.setValue(service.position)
        with QSignalBlocker(self.volume), QSignalBlocker(self.mute):
            self.volume.setValue(service.volume)
            self.mute.setChecked(service.muted)
        self.time.setText(self.vm.time_label)
