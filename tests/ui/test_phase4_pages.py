from auravlian.domain.models.track import Track
from auravlian.presentation.pages.collections import CollectionPage
from auravlian.presentation.pages.library import LibraryPage
from PySide6.QtWidgets import QMessageBox


def ready(qtbot, container):
    qtbot.waitUntil(lambda: not container.library.service.busy and not container.collections.service.busy,
                    timeout=10_000)


def seed(qtbot, container, tmp_path):
    ready(qtbot, container)
    tracks = [Track(tmp_path / f"{i}.wav", f"Track {i}", f"Artist {i % 2}", "Album", 1000)
              for i in range(3)]
    container.library.service.repository.upsert(tracks)
    container.library.service.start()
    ready(qtbot, container)
    return tracks


def test_phase4_album_artist_groups_and_shared_playback(window, qtbot, container, tmp_path, monkeypatch):
    tracks = seed(qtbot, container, tmp_path)
    albums, artists = window.pages["Albums"], window.pages["Artists"]
    assert isinstance(albums, CollectionPage) and isinstance(artists, CollectionPage)
    assert albums.selector.count() == 2 and artists.selector.count() == 2
    assert albums.vm.library.playback is window.player_vm.service
    played = []
    monkeypatch.setattr(window.player_vm.service, "open_tracks", lambda rows: played.extend(rows))
    artists.selector.setCurrentRow(0)
    artists.play_all()
    assert len(played) == 2
    assert all(t.artist == tracks[0].artist for t in played)


def test_phase4_create_favorite_playlist_reorder_and_remove(window, qtbot, container, tmp_path, monkeypatch):
    tracks = seed(qtbot, container, tmp_path)
    page = window.pages["Playlists"]
    assert isinstance(page, CollectionPage)
    monkeypatch.setattr("auravlian.presentation.pages.collections.QInputDialog.getText",
                        lambda *args, **kwargs: ("My playlist", True))
    page.create_playlist()
    ready(qtbot, container)
    playlist_id = page.playlist_id()
    assert playlist_id is not None
    container.collections.service.add(playlist_id, [t.path for t in tracks])
    container.collections.service.favorite([tracks[0].path], True)
    ready(qtbot, container)
    assert page.model.rowCount() == 3
    page.table.selectRow(0)
    page.move_track(1)
    ready(qtbot, container)
    assert page.model.tracks[1].path == tracks[0].path
    page.remove()
    ready(qtbot, container)
    assert page.model.rowCount() == 2
    favorites = window.pages["Favorites"]
    assert isinstance(favorites, CollectionPage)
    assert favorites.model.rowCount() == 1
    favorites.table.selectRow(0)
    favorites.unfavorite()
    ready(qtbot, container)
    assert favorites.model.rowCount() == 0


def test_phase4_library_actions_and_history_pages(window, qtbot, container, tmp_path):
    tracks = seed(qtbot, container, tmp_path)
    page = window.pages["Library"]
    assert isinstance(page, LibraryPage)
    page.table.selectRow(0)
    page._favorite()
    ready(qtbot, container)
    assert len(container.collections.service.snapshot.favorites) == 1
    container.collections.service.record(tracks[0])
    ready(qtbot, container)
    history = window.pages["Recently Played"]
    assert isinstance(history, CollectionPage)
    assert history.model.rowCount() == 1
    assert "1 playback starts" in history.status.text()
    window.navigate("Recently Played")
    assert window.playback_bar.isVisible()


def test_phase4_rename_delete_and_edits_preserve_session_queue(window, qtbot, container, tmp_path, monkeypatch):
    tracks = seed(qtbot, container, tmp_path)
    player = window.player_vm.service
    player.queue.replace(tracks)
    page = window.pages["Playlists"]
    container.collections.service.create("Original")
    ready(qtbot, container)
    monkeypatch.setattr("auravlian.presentation.pages.collections.QInputDialog.getText",
                        lambda *args, **kwargs: ("Renamed", True))
    page.rename()
    ready(qtbot, container)
    assert container.collections.service.snapshot.playlists[0].name == "Renamed"
    monkeypatch.setattr("auravlian.presentation.pages.collections.QMessageBox.question",
                        lambda *args: QMessageBox.StandardButton.Yes)
    page.delete()
    ready(qtbot, container)
    assert container.collections.service.snapshot.playlists == []
    assert player.queue.tracks == tuple(tracks)
    assert len(container.library.service.tracks) == 3


def test_phase4_duplicate_name_error_visible(window, qtbot, container):
    ready(qtbot, container)
    container.collections.service.create("Duplicate")
    ready(qtbot, container)
    container.collections.service.create("duplicate")
    qtbot.waitUntil(lambda: not container.collections.service.busy)
    assert "already exists" in window.pages["Playlists"].status.text()
