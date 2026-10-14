from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit,
    QPushButton, QTableView, QVBoxLayout, QWidget,
)

from auravlian.presentation.pages.base import label
from auravlian.presentation.viewmodels.library_vm import LibraryViewModel
from auravlian.presentation.widgets.track_table import TrackTableModel, TrackFilterModel


class LibraryPage(QWidget):
    def __init__(self, vm: LibraryViewModel) -> None:
        super().__init__()
        self.vm = vm
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(16)
        layout.addWidget(label("YOUR MUSIC, BEAUTIFULLY TOGETHER", "eyebrow"))
        layout.addWidget(label("Music Library", "title"))
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search title, artist or album…")
        self.search.setAccessibleName("Search library")
        toolbar.addWidget(self.search, 1)
        self.import_files = QPushButton("Import files")
        self.import_folder = QPushButton("Import folder")
        self.rescan = QPushButton("Rescan")
        self.cancel = QPushButton("Cancel")
        for button in (self.import_files, self.import_folder, self.rescan, self.cancel):
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.status = label("", "subtitle")
        layout.addWidget(self.status)
        self.empty = label("No music imported. Add local audio files or a folder to begin.", "section")
        layout.addWidget(self.empty)
        self.model = TrackTableModel()
        self.proxy = TrackFilterModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft |
                                                         Qt.AlignmentFlag.AlignVCenter)
        self.table.setAccessibleName("Music library tracks")
        layout.addWidget(self.table, 1)
        self.play_selected = QPushButton("Play selected")
        self.play_selected.setObjectName("primary")
        layout.addWidget(self.play_selected)
        self.search.textChanged.connect(self.proxy.search)
        self.proxy.rowsInserted.connect(self._empty_state)
        self.proxy.rowsRemoved.connect(self._empty_state)
        self.search.textChanged.connect(self._empty_state)
        self.table.selectionModel().selectionChanged.connect(self._selection)
        self.play_selected.clicked.connect(self._play_selection)
        self.table.doubleClicked.connect(self._play_row)
        self.import_files.clicked.connect(self._files)
        self.import_folder.clicked.connect(self._folder)
        self.rescan.clicked.connect(lambda: vm.service.start("rescan"))
        self.cancel.clicked.connect(vm.service.cancel)
        vm.changed.connect(self.refresh)
        self.refresh()
        vm.service.start()

    def refresh(self) -> None:
        service = self.vm.service
        self.model.replace(service.tracks)
        self.status.setText(service.status)
        self.status.setToolTip("\n".join(service.last_result.warnings))
        for button in (self.import_files, self.import_folder, self.rescan):
            button.setEnabled(not service.busy)
        self.cancel.setEnabled(service.busy)
        self._empty_state()
        self._selection()

    def _empty_state(self, *args) -> None:
        self.empty.setVisible(self.proxy.rowCount() == 0)
        self.empty.setText("No matching tracks." if self.model.rowCount() else
                           "No music imported. Add local audio files or a folder to begin.")

    def _selection(self, *args) -> None:
        rows = self.table.selectionModel().selectedRows()
        self.play_selected.setEnabled(any(
            not self.model.tracks[self.proxy.mapToSource(row).row()].missing for row in rows))

    def _play_selection(self) -> None:
        rows = sorted(self.table.selectionModel().selectedRows(), key=lambda index: index.row())
        self.vm.play([self.model.tracks[self.proxy.mapToSource(row).row()] for row in rows])

    def _play_row(self, index) -> None:
        if not index.isValid():
            return
        track = self.model.tracks[self.proxy.mapToSource(index).row()]
        self.vm.play([track])

    def _files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Import audio files", "",
            "Audio (*.mp3 *.flac *.wav *.ogg *.m4a *.aac *.wma *.opus *.aiff *.aif);;All files (*)")
        if paths:
            self.vm.import_paths([Path(path) for path in paths])

    def _folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Import music folder")
        if path:
            self.vm.import_paths([Path(path)])
