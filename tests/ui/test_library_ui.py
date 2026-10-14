from pathlib import Path
from threading import Event

from PySide6.QtCore import Qt

from auravlian.domain.models.track import Track
from auravlian.presentation.pages.library import LibraryPage
from auravlian.presentation.widgets.track_table import TrackTableModel, TrackFilterModel
from auravlian.application.search_service import matches


def test_model_search_sort_and_thousands_of_rows(qapp):
    model = TrackTableModel()
    model.replace([Track(Path(f"{i}.wav"), f"Song {i}", "Artist", "Album", i * 1000)
                   for i in range(5000)])
    proxy = TrackFilterModel()
    proxy.setSourceModel(model)
    proxy.setSortRole(Qt.ItemDataRole.UserRole)
    assert proxy.rowCount() == 5000
    proxy.search("SONG 4999 artist")
    assert proxy.rowCount() == 1
    assert proxy.index(0, 0).data() == "Song 4999"
    proxy.search("")
    proxy.sort(3, Qt.SortOrder.DescendingOrder)
    assert proxy.index(0, 3).data() == "83:19"
    assert model.headerData(0, Qt.Orientation.Horizontal) == "Title"
    assert matches(model.tracks[0], "artist album")
    assert not matches(model.tracks[0], "absent")


def test_library_ui_state_search_and_shared_playback(window, qtbot, monkeypatch):
    page = window.pages["Library"]
    assert isinstance(page, LibraryPage)
    service = page.vm.service
    qtbot.waitUntil(lambda: not service.busy)
    service.tracks = [Track(Path("one.wav"), "Aurora", "Artist", "Album", 6000),
                      Track(Path("lost.wav"), "Lost", missing=True)]
    service.changed.emit()
    window.navigate("Library")
    assert page.model.rowCount() == 2
    page.search.setText("aurora")
    assert page.proxy.rowCount() == 1
    page.table.selectRow(0)
    assert page.play_selected.isEnabled()
    selected = []
    monkeypatch.setattr(window.player_vm.service, "open_tracks", lambda tracks: selected.extend(tracks))
    qtbot.mouseClick(page.play_selected, Qt.MouseButton.LeftButton)
    assert selected[0].title == "Aurora"
    assert page.vm.playback is window.player_vm.service
    page.search.setText("lost")
    page.table.selectRow(0)
    assert not page.play_selected.isEnabled()
    page.search.setText("nothing")
    assert page.empty.isVisible()


def test_file_dialog_import_and_cancel(window, qtbot, monkeypatch, tmp_path):
    page = window.pages["Library"]
    qtbot.waitUntil(lambda: not page.vm.service.busy)
    calls = []
    monkeypatch.setattr(page.vm, "import_paths", lambda paths: calls.append(paths))
    monkeypatch.setattr("auravlian.presentation.pages.library.QFileDialog.getOpenFileNames",
                        lambda *args: ([str(tmp_path / "music.wav")], ""))
    page._files()
    assert calls == [[tmp_path / "music.wav"]]
    monkeypatch.setattr("auravlian.presentation.pages.library.QFileDialog.getExistingDirectory",
                        lambda *args: "")
    page._folder()
    assert len(calls) == 1


def test_close_cancels_worker_before_destroying_window(window, qtbot, tmp_path):
    service = window.container.library.service
    qtbot.waitUntil(lambda: not service.busy)
    entered, release = Event(), Event()
    path = tmp_path / "slow.wav"
    path.write_bytes(b"reader is isolated in this close/cancellation test")

    def slow_reader(path):
        entered.set()
        assert release.wait(5)
        return Track(path)

    service.reader = slow_reader
    try:
        service.start("import", [path])
        qtbot.waitUntil(entered.is_set)
        window.close()
        assert window.isVisible()
        release.set()
        qtbot.waitUntil(lambda: not window.isVisible())
        assert not service.busy and service.last_result.cancelled
    finally:
        release.set()
        service.shutdown()
