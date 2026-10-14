from PySide6.QtCore import QSignalBlocker, Qt, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor
from pathlib import Path
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QInputDialog, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget, QFileDialog, QFrame, QLabel,
    QLineEdit, QMenu, QToolButton,
)

from auravlian.domain.models.track import Track
from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.playlist_vm import CollectionViewModel
from auravlian.presentation.widgets.track_table import TrackTableModel
from auravlian.presentation.widgets.favorite_table import FavoriteTableModel
from auravlian.application.search_service import matches


class CollectionPage(QWidget):
    """Album/artist drill-down, ordered playlists, favorites and recent local plays."""
    library_requested = Signal()

    def __init__(self, kind: str, vm: CollectionViewModel) -> None:
        super().__init__()
        self.kind, self.vm = kind, vm
        self.groups: dict[object, list[Track]] = {}
        self._snapshot: tuple[int, int] | None = None
        self.importing = False
        self.playlist_detail = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(16)
        layout.addWidget(label("Favorite tracks" if kind == "Favorites" else kind, "title"))
        self.status = label("", "subtitle")
        layout.addWidget(self.status)
        self.album_header = QFrame()
        self.album_header.setObjectName("hero")
        album_layout = QHBoxLayout(self.album_header)
        album_layout.setContentsMargins(20, 16, 20, 16)
        self.album_cover = QLabel("♫")
        self.album_cover.setObjectName("musicCover")
        self.album_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_cover.setFixedSize(112, 112)
        album_layout.addWidget(self.album_cover)
        album_info = QVBoxLayout()
        self.album_title = label("", "section")
        self.album_title.setWordWrap(True)
        self.album_detail = label("", "subtitle")
        self.album_detail.setWordWrap(True)
        album_info.addWidget(self.album_title)
        album_info.addWidget(self.album_detail)
        album_layout.addLayout(album_info, 1)
        layout.addWidget(self.album_header)
        toolbar = QHBoxLayout()
        editbar = QHBoxLayout()
        self.buttons: dict[str, QPushButton] = {}
        self.back = QPushButton("← All playlists")
        self.back.clicked.connect(self.show_overview)
        toolbar.addWidget(self.back)
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
        toolbar.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter playlists…" if kind == "Playlists" else "Filter tracks…")
        self.search.setAccessibleName(f"Filter {kind}")
        self.search.setMaximumWidth(300)
        self.search.textChanged.connect(self.filter_content)
        toolbar.addWidget(self.search)
        if kind == "Favorites":
            self.buttons["Play all"].setText("▶")
            self.buttons["Play all"].setFixedSize(40, 40)
            self.buttons["Play all"].setToolTip("Play favorite tracks")
            self.buttons["Play all"].setAccessibleName("Play favorite tracks")
            add_favorite = QPushButton("+")
            add_favorite.setFixedSize(40, 40)
            add_favorite.setToolTip("Add favorites from Library")
            add_favorite.setAccessibleName("Add favorites from Library")
            add_favorite.clicked.connect(self.library_requested)
            toolbar.insertWidget(2, add_favorite)
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
            toolbar.insertWidget(0, self.buttons["New"])
            toolbar.insertWidget(1, self.buttons["Import M3U"])
            self.more = QToolButton()
            self.more.setText("•••")
            self.more.setAccessibleName("Playlist actions")
            self.more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            self.more_menu = QMenu(self.more)
            self.menu_actions = {}
            for name in ("Rename", "Delete", "Remove", "Move up", "Move down", "Export M3U"):
                menu_action = self.more_menu.addAction(name)
                menu_action.triggered.connect(self.buttons[name].click)
                self.menu_actions[name] = menu_action
            self.more.setMenu(self.more_menu)
            toolbar.addWidget(self.more)
        body = QHBoxLayout()
        self.selector = QListWidget()
        self.selector.setMaximumWidth(220)
        self.selector.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.selector.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.selector.setAccessibleName(f"{kind} groups")
        if kind == "Playlists":
            self.selector.setViewMode(QListWidget.ViewMode.IconMode)
            self.selector.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.selector.setMovement(QListWidget.Movement.Static)
            self.selector.setWrapping(True)
            self.selector.setIconSize(QSize(144, 144))
            self.selector.setGridSize(QSize(176, 210))
            self.selector.setSpacing(10)
            self.selector.setObjectName("playlistGallery")
            self.selector.itemClicked.connect(lambda _: self.open_playlist())
            self.selector.itemActivated.connect(lambda _: self.open_playlist())
        self.selector.setVisible(kind in ("Albums", "Artists", "Playlists"))
        self.selector.currentRowChanged.connect(self.load_group)
        body.addWidget(self.selector)
        self.model = FavoriteTableModel() if kind == "Favorites" else TrackTableModel()
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
        self.table.setIconSize(QSize(40, 40))
        if kind == "Favorites":
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(0, 36)
            self.table.clicked.connect(lambda index: self.unfavorite_at(index.row()) if index.column() == 0 else None)
        self.table.setAccessibleName(f"{kind} tracks")
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)
        self.table.doubleClicked.connect(lambda index: self.vm.play([self.model.tracks[index.row()]]))
        body.addWidget(self.table, 1, Qt.AlignmentFlag.AlignTop if kind == "Favorites" else Qt.AlignmentFlag(0))
        layout.addLayout(body, 1)
        self.empty = label("", "subtitle")
        layout.addWidget(self.empty)
        vm.changed.connect(self.refresh)
        self.refresh()

    def unfavorite_at(self, row: int) -> None:
        if not self.vm.service.busy and 0 <= row < len(self.model.tracks):
            self.vm.service.favorite([self.model.tracks[row].path], False)

    def open_playlist(self) -> None:
        self.playlist_detail = True
        self.search.clear()
        self.search.setPlaceholderText("Filter tracks…")
        self.load_group()

    def show_overview(self) -> None:
        self.playlist_detail = False
        self.search.clear()
        self.search.setPlaceholderText("Filter playlists…")
        self.load_group()

    def filter_content(self, text: str) -> None:
        if self.kind == "Playlists" and not self.playlist_detail:
            for row in range(self.selector.count()):
                item = self.selector.item(row)
                item.setHidden(text.casefold() not in item.text().casefold())
        else:
            self.load_group()

    def update_layout(self) -> None:
        overview = self.kind == "Playlists" and not self.playlist_detail
        self.back.setVisible(self.kind == "Playlists" and self.playlist_detail)
        self.table.setVisible(not overview)
        if self.kind == "Playlists":
            self.selector.setVisible(overview)
            self.selector.setMaximumWidth(16777215 if overview else 220)
            for name, button in self.buttons.items():
                button.setVisible(name in ("New", "Import M3U") if overview else
                                  name in ("Play selected", "Play all"))
            self.more.setVisible(not overview)
            self.buttons["New"].setText("+ Create new")
        self.album_header.setVisible(not overview and bool(self.model.tracks)
                                     and self.kind in ("Albums", "Artists", "Playlists"))
        if self.kind == "Favorites":
            self.buttons["Play selected"].hide()
            self.buttons["Remove favorites"].hide()
        if overview:
            self.empty.setText("Create a playlist to start your collection." if not self.selector.count() else "")

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
                    if self.kind == "Playlists":
                        item.setText(f"{names[group_key]}\n{len(tracks)} tracks")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
                        artwork = next((t.artwork_path for t in tracks if t.artwork_path), "")
                        if artwork:
                            item.setIcon(QIcon(artwork))
                        else:
                            from auravlian.presentation.theme.tokens import TOKENS
                            fallback = QPixmap(144, 144)
                            fallback.fill(QColor(TOKENS["surface"]))
                            painter = QPainter(fallback)
                            painter.setPen(QColor(TOKENS["muted"]))
                            font = painter.font()
                            font.setPixelSize(64)
                            painter.setFont(font)
                            painter.drawText(fallback.rect(), Qt.AlignmentFlag.AlignCenter, "♫")
                            painter.end()
                            item.setIcon(QIcon(fallback))
                        item.setSizeHint(QSize(166, 200))
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
        if self.search.text() and not (self.kind == "Playlists" and not self.playlist_detail):
            tracks = [t for t in tracks if matches(t, self.search.text())]
        self.model.replace(tracks)
        if self.kind == "Favorites":
            self.table.setMaximumHeight(min(480, 48 * (len(tracks) + 1) + 8))
            self.status.setVisible(bool(self.vm.service.error) or self.vm.service.busy)
        self.album_header.setVisible(bool(tracks) and self.kind in ("Albums", "Artists", "Playlists"))
        self.album_title.setText(str(item.text().splitlines()[0].rsplit("  ·  ", 1)[0]) if item else self.kind)
        self.album_detail.setText(f"{len(tracks)} tracks · {sum(t.duration_ms for t in tracks) // 60000} min · Local collection")
        self.album_cover.clear()
        artwork = next((t.artwork_path for t in tracks if t.artwork_path), "")
        pixmap = QPixmap(artwork) if artwork else QPixmap()
        if pixmap.isNull():
            self.album_cover.setText("♫")
        else:
            self.album_cover.setPixmap(pixmap.scaled(112, 112, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))
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
        self.update_layout()

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
            self.buttons["Move up"].setEnabled(row > 0 and not busy and not self.search.text())
            self.buttons["Move down"].setEnabled(0 <= row < len(self.model.tracks) - 1 and not busy and not self.search.text())
            for name, action in self.menu_actions.items():
                action.setEnabled(self.buttons[name].isEnabled())
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
