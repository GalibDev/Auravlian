from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout


class PlaybackBar(QFrame):
    """Honest visual shell; no simulated playback state."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playback")
        self.setMinimumHeight(108)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        info = QVBoxLayout()
        info.addWidget(QLabel("Nothing playing"))
        caption = QLabel("Local playback arrives in Phase 2")
        caption.setObjectName("subtitle")
        info.addWidget(caption)
        layout.addLayout(info, 2)
        middle = QVBoxLayout()
        buttons = QHBoxLayout()
        for name in ("Shuffle", "Previous", "Play", "Next", "Repeat"):
            button = QPushButton(name)
            button.setEnabled(False)
            button.setAccessibleName(name)
            button.setToolTip("Available in Phase 2 — audio playback")
            buttons.addWidget(button)
        middle.addLayout(buttons)
        seek = QSlider(Qt.Orientation.Horizontal)
        seek.setAccessibleName("Playback position")
        seek.setEnabled(False)
        middle.addWidget(seek)
        layout.addLayout(middle, 4)
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setAccessibleName("Playback volume")
        volume.setMaximumWidth(100)
        volume.setEnabled(False)
        layout.addWidget(QLabel("Volume"))
        layout.addWidget(volume)

