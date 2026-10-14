from PySide6.QtCore import QSignalBlocker, Qt
from pathlib import Path
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QInputDialog, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget, QFileDialog,
)

from auravlian.domain.models.track import Track
from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.playlist_vm import CollectionViewModel
from auravlian.presentation.widgets.track_table import TrackTableModel


class CollectionPage(QWidget):
    """Album/artist drill-down, ordered playlists, favorites and recent local plays."""

    def __init__(self, kind: str, vm: CollectionViewModel) -> None:
        super().__init__()
        self.kind, self.vm = kind, vm
        self.groups: dict[object, list[Track]] = {}
        self._snapshot: tuple[int, int] | None = None
        self.importing = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(16)
        layout.addWidget(label("YOUR COLLECTION, YOUR WAY", "eyebrow"))
        layout.addWidget(label(kind, "title"))
        self.status = label("", "subtitle")
        layout.addWidget(self.status)
        toolbar = QHBoxLayout()
        editbar = QHBoxLayout()
        self.buttons: dict[str, QPushButton] = {}
        actions = [("Play selected", self.play_selected), ("Play all", self.play_all)]
        if kind == "Playlists":
            actions += [("New", self.create_playlist), ("Rename", self.rename), ("Delete", self.delete),
                        ("Remove", self.remove), ("Move up", lambda: self.move_track(-1)),
                        ("Move down", lambda: self.move_track(1))]
        elif kind == "Favorites":
            actions += [("Remove favorites", self.unfavorite)]
        for name, action in actions:
            button = QPushButton(name)
            button.clicked.connect(action)
            (toolbar if name.startswith("Play ") else editbar).addWidget(button)
            self.buttons[name] = button
        layout.addLayout(toolbar)
        if kind in ("Playlists", "Favorites"):
            layout.addLayout(editbar)
        if kind == "Playlists":
            playlist_io = QHBoxLayout()
            for name, action in (("Import M3U", self.import_playlist), ("Export M3U", self.export_playlist)):
                button = QPushButton(name)
                button.clicked.connect(action)
                self.buttons[name] = button
                playlist_io.addWidget(button)
            layout.addLayout(playlist_io)
        body = QHBoxLayout()
        self.selector = QListWidget()
        self.selector.setMaximumWidth(220)
        self.selector.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.selector.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.selector.setAccessibleName(f"{kind} groups")
        self.selector.setVisible(kind in ("Albums", "Artists", "Playlists"))
        self.selector.currentRowChanged.connect(self.load_group)
        body.addWidget(self.selector)
        self.model = TrackTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAccessibleName(f"{kind} tracks")
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)
        self.table.doubleClicked.connect(lambda index: self.vm.play([self.model.tracks[index.row()]]))
        body.addWidget(self.table, 1)
        layout.addLayout(body, 1)
        self.empty = label("", "subtitle")
        layout.addWidget(self.empty)
        vm.changed.connect(self.refresh)
        self.refresh()

    def selected_tracks(self) -> list[Track]:
        rows = sorted(self.table.selectionModel().selectedRows(), key=lambda row: row.row())
        return [self.model.tracks[row.row()] for row in rows]

    def playlist_id(self) -> int | None:
        item = self.selector.currentItem()
        return int(item.data(Qt.ItemDataRole.UserRole)) if item and self.kind == "Playlists" else None

    def refresh(self) -> None:
        service = self.vm.service
        if self.importing and not service.busy:
            self.importing = False
            if not service.error:
                self.vm.library.service.start()
        self.status.setText(service.error or ("Saving collection…" if service.busy else
                            (f"{service.snapshot.play_count} playback starts · latest 200 tracks"
                             if self.kind == "Recently Played" else "Stored locally on this computer")))
        # Avoid resetting selection on busy-only notifications.
        token = (id(service.snapshot), id(self.vm.library.service.tracks))
        if token != self._snapshot:
            self._snapshot = token
            previous = self.selector.currentItem()
            key = previous.data(Qt.ItemDataRole.UserRole) if previous else None
            with QSignalBlocker(self.selector):
                self.selector.clear()
                names: dict[object, str]
                if self.kind == "Playlists":
                    self.groups = {p.id: list(p.tracks) for p in service.snapshot.playlists}
                    names = {p.id: p.name for p in service.snapshot.playlists}
                elif self.kind in ("Albums", "Artists"):
                    self.groups = {key: tracks for key, tracks in self.vm.groups(self.kind).items()}
                    names = {key: str(key) for key in self.groups}
                else:
                    tracks = service.snapshot.favorites if self.kind == "Favorites" else service.snapshot.history
                    self.groups, names = {"all": tracks}, {}
                current = 0
                for row, (group_key, tracks) in enumerate(self.groups.items()):
                    if not names:
                        break
                    item = QListWidgetItem(f"{names[group_key]}  ·  {len(tracks)} tracks")
                    item.setToolTip(f"{names[group_key]} · {len(tracks)} tracks")
                    item.setData(Qt.ItemDataRole.UserRole, group_key)
                    self.selector.addItem(item)
                    if group_key == key:
                        current = row
                self.selector.setCurrentRow(current)
            self.load_group()
        self.selection_changed()

    def load_group(self, *args) -> None:
        selected = {str(track.path) for track in self.selected_tracks()}
        item = self.selector.currentItem()
        key = item.data(Qt.ItemDataRole.UserRole) if item else "all"
        tracks = self.groups.get(key, [])
        self.model.replace(tracks)
        # Keep a single row selected after a reorder, without changing the queue.
        if len(selected) == 1:
            for index, track in enumerate(tracks):
                if str(track.path) in selected:
                    self.table.selectRow(index)
                    break
        self.empty.setText("" if tracks else (
            "Create a playlist, then add songs from Music Library." if self.kind == "Playlists" else
            "Favorite songs from Music Library to keep them here." if self.kind == "Favorites" else
            "Your real playback history will appear here." if self.kind == "Recently Played" else
            "Import music in Library to browse this collection."))
        self.selection_changed()

    def selection_changed(self, *args) -> None:
        selected = self.selected_tracks()
        busy = self.vm.service.busy
        self.buttons["Play selected"].setEnabled(any(not t.missing for t in selected))
        self.buttons["Play all"].setEnabled(any(not t.missing for t in self.model.tracks))
        if self.kind == "Playlists":
            valid = self.playlist_id() is not None
            for name in ("Rename", "Delete"):
                self.buttons[name].setEnabled(valid and not busy)
            self.buttons["New"].setEnabled(not busy)
            self.buttons["Import M3U"].setEnabled(not busy and not self.vm.library.service.busy)
            self.buttons["Export M3U"].setEnabled(valid and not busy)
            self.buttons["Remove"].setEnabled(bool(selected) and not busy)
            rows = self.table.selectionModel().selectedRows()
            row = rows[0].row() if len(rows) == 1 else -1
            self.buttons["Move up"].setEnabled(row > 0 and not busy)
            self.buttons["Move down"].setEnabled(0 <= row < len(self.model.tracks) - 1 and not busy)
        if self.kind == "Favorites":
            self.buttons["Remove favorites"].setEnabled(bool(selected) and not busy)

    def play_selected(self) -> None:
        self.vm.play(self.selected_tracks())

    def play_all(self) -> None:
        self.vm.play(self.model.tracks)

    def create_playlist(self) -> None:
        name, accepted = QInputDialog.getText(self, "New playlist", "Playlist name")
        if accepted:
            self.vm.service.create(name)

    def rename(self) -> None:
        playlist_id = self.playlist_id()
        if playlist_id is not None:
            playlist = next(p for p in self.vm.service.snapshot.playlists if p.id == playlist_id)
            name, accepted = QInputDialog.getText(self, "Rename playlist", "Playlist name", text=playlist.name)
            if accepted:
                self.vm.service.rename(playlist_id, name)

    def delete(self) -> None:
        playlist_id = self.playlist_id()
        if playlist_id is not None and QMessageBox.question(
                self, "Delete playlist", "Delete this playlist? Your audio files will be kept.") == QMessageBox.StandardButton.Yes:
            self.vm.service.delete(playlist_id)

    def remove(self) -> None:
        playlist_id = self.playlist_id()
        if playlist_id is not None:
            self.vm.service.remove(playlist_id, [t.path for t in self.selected_tracks()])

    def move_track(self, offset: int) -> None:
        rows = self.table.selectionModel().selectedRows()
        playlist_id = self.playlist_id()
        if len(rows) != 1 or playlist_id is None:
            return
        row = rows[0].row()
        target = row + offset
        if 0 <= target < len(self.model.tracks):
            paths = [t.path for t in self.model.tracks]
            paths[row], paths[target] = paths[target], paths[row]
            self.vm.service.reorder(playlist_id, paths)

    def unfavorite(self) -> None:
        self.vm.service.favorite([t.path for t in self.selected_tracks()], False)

    def import_playlist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import local playlist", "", "M3U (*.m3u *.m3u8)")
        if path:
            self.importing = True
            library = self.vm.library.service
            self.vm.service.import_m3u(Path(path), library.repository, library.reader)

    def export_playlist(self) -> None:
        playlist_id = self.playlist_id()
        if playlist_id is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export playlist", "playlist.m3u8", "M3U8 (*.m3u8)")
        if path:
            self.vm.service.export_m3u(playlist_id, Path(path))
