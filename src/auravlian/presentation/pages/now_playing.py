from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget

from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class NowPlayingPage(QWidget):
    open_requested = Signal()

    def __init__(self, vm: PlayerViewModel) -> None:
        super().__init__()
        self.vm = vm
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)
        layout.addWidget(label("GIVE THE MUSIC YOUR FULL ATTENTION", "eyebrow"))
        layout.addWidget(label("Now Playing", "title"))
        card = QFrame()
        card.setObjectName("hero")
        body = QVBoxLayout(card)
        body.setContentsMargins(32, 40, 32, 40)
        self.track = label("", "title")
        self.status = label("", "subtitle")
        self.time = label("", "section")
        body.addWidget(self.track)
        body.addWidget(self.status)
        body.addWidget(self.time)
        open_button = QPushButton("Open audio files…")
        open_button.setObjectName("primary")
        open_button.clicked.connect(self.open_requested)
        body.addWidget(open_button)
        layout.addWidget(card)
        layout.addWidget(label("Use the playback bar below. Files opened here replace the current "
                               "session queue; your music stays on your computer.", "subtitle"))
        layout.addStretch()
        vm.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.track.setText(self.vm.title)
        self.status.setText(self.vm.subtitle)
        self.time.setText(self.vm.time_label)
