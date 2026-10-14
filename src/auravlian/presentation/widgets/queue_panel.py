from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from auravlian.domain.models.track import Track
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel


class QueuePanel(QDialog):
    def __init__(self, vm: PlayerViewModel, parent=None) -> None:
        super().__init__(parent)
        self.vm = vm
        self.setObjectName("queuePanel")
        self.token: tuple[tuple[Track, ...], Track | None] | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        heading = QLabel("Up next")
        heading.setObjectName("section")
        layout.addWidget(heading)
        self.empty = QLabel("Open audio files or play a song from your library.")
        self.empty.setWordWrap(True)
        self.empty.setObjectName("subtitle")
        layout.addWidget(self.empty)
        self.list = QListWidget()
        self.list.setIconSize(QSize(42, 42))
        self.list.setAccessibleName("Playback queue tracks")
        layout.addWidget(self.list)
        self.buttons: dict[str, QPushButton] = {}
        for name, action in (("Play selected", self.play_selected), ("Remove", self.remove_selected),
                             ("Clear queue", vm.service.clear_queue)):
            button = QPushButton(name)
            button.clicked.connect(action)
            self.buttons[name] = button
            layout.addWidget(button)
        self.list.currentRowChanged.connect(self.update_actions)
        self.list.itemDoubleClicked.connect(lambda _: self.play_selected())
        vm.changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        queue = self.vm.service.queue
        token = (queue.ordered_tracks, queue.current)
        if token != self.token:
            selected = self.list.currentRow()
            self.token = token
            self.list.clear()
            for track in queue.ordered_tracks:
                prefix = "▶  " if track == queue.current else ""
                duration = f"{track.duration_ms // 60000}:{track.duration_ms // 1000 % 60:02d}"
                item = QListWidgetItem(f"{prefix}{track.title}\n{track.artist}  ·  {duration}")
                if track.artwork_path:
                    item.setIcon(QIcon(track.artwork_path))
                item.setToolTip(f"{track.title} — {track.artist}")
                self.list.addItem(item)
            if selected >= 0:
                self.list.setCurrentRow(min(selected, self.list.count() - 1))
            self.empty.setVisible(not queue.ordered_tracks)
        self.update_actions()

    def update_actions(self) -> None:
        selected = self.list.currentRow() >= 0
        self.buttons["Play selected"].setEnabled(selected)
        self.buttons["Remove"].setEnabled(selected)
        self.buttons["Clear queue"].setEnabled(bool(self.vm.service.queue.ordered_tracks))

    def play_selected(self) -> None:
        self.vm.service.select_queue(self.list.currentRow())

    def remove_selected(self) -> None:
        self.vm.service.remove_queue(self.list.currentRow())
