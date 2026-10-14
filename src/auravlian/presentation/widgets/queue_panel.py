from PySide6.QtWidgets import QDialog, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton

from auravlian.presentation.viewmodels.player_vm import PlayerViewModel
from auravlian.domain.models.track import Track


class QueuePanel(QDialog):
    def __init__(self, vm: PlayerViewModel, parent=None) -> None:
        super().__init__(parent)
        self.vm = vm
        self.setWindowTitle("Auravlian — Playback queue")
        self.resize(550, 500)
        self.token: tuple[tuple[Track, ...], Track | None] | None = None
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.setAccessibleName("Playback queue tracks")
        layout.addWidget(self.list)
        actions = QHBoxLayout()
        for name, action in (("Play selected", self.play_selected), ("Remove", self.remove_selected),
                             ("Clear queue", vm.service.clear_queue)):
            button = QPushButton(name)
            button.clicked.connect(action)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.list.itemDoubleClicked.connect(lambda _: self.play_selected())
        vm.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        queue = self.vm.service.queue
        token = (queue.ordered_tracks, queue.current)
        if token != self.token:
            self.token = token
            self.list.clear()
            self.list.addItems([("▶  " if track == queue.current else "") + track.title
                                for track in queue.ordered_tracks])

    def play_selected(self) -> None:
        self.vm.service.select_queue(self.list.currentRow())

    def remove_selected(self) -> None:
        self.vm.service.remove_queue(self.list.currentRow())
