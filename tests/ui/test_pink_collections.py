from PySide6.QtCore import Qt

from auravlian.domain.models.track import Track
from auravlian.presentation.theme.tokens import TOKENS


def settle(qtbot, container):
    qtbot.waitUntil(lambda: not container.library.service.busy and not container.collections.service.busy,
                    timeout=10000)


def seed(qtbot, container, tmp_path):
    settle(qtbot, container)
    track = Track(tmp_path / "sample.wav", "A local song", "Test artist", duration_ms=5000)
    container.library.service.repository.upsert([track])
    container.library.service.start()
    settle(qtbot, container)
    return track


def test_playlist_gallery_filter_open_and_back(window, qtbot, container, tmp_path):
    track = seed(qtbot, container, tmp_path)
    container.collections.service.create("My songs")
    settle(qtbot, container)
    page = window.pages["Playlists"]
    container.collections.service.add(page.playlist_id(), [track.path])
    settle(qtbot, container)
    window.navigate("Playlists")
    assert page.selector.isVisible() and not page.table.isVisible()
    assert not page.buttons["Rename"].isVisible()
    page.search.setText("no match")
    assert page.selector.item(0).isHidden()
    page.search.clear()
    qtbot.mouseClick(page.selector.viewport(), Qt.MouseButton.LeftButton,
                     pos=page.selector.visualItemRect(page.selector.item(0)).center())
    assert page.table.isVisible() and not page.selector.isVisible()
    assert page.model.tracks == [track]
    assert page.more.isVisible()
    page.show_overview()
    assert page.selector.isVisible() and not page.table.isVisible()


def test_favorite_filter_and_heart_remove(window, qtbot, container, tmp_path):
    track = seed(qtbot, container, tmp_path)
    container.collections.service.favorite([track.path], True)
    settle(qtbot, container)
    page = window.pages["Favorites"]
    window.navigate("Favorites")
    assert page.model.HEADERS == ("♥", "Artist", "Title", "Duration")
    page.search.setText("absent")
    assert page.model.rowCount() == 0
    page.search.setText("Test artist")
    assert page.model.rowCount() == 1
    page.unfavorite_at(0)
    settle(qtbot, container)
    assert page.model.rowCount() == 0


def test_player_heart_persists_and_tracks_current_song(window, qtbot, container, tmp_path):
    track = seed(qtbot, container, tmp_path)
    container.player.service.queue.replace([track])
    container.player.changed.emit()
    assert window.playback_bar.favorite.isEnabled()
    qtbot.mouseClick(window.playback_bar.favorite, Qt.MouseButton.LeftButton)
    settle(qtbot, container)
    assert window.playback_bar.favorite.isChecked()
    assert container.collections.service.snapshot.favorites == [track]
    qtbot.mouseClick(window.playback_bar.favorite, Qt.MouseButton.LeftButton)
    settle(qtbot, container)
    assert not window.playback_bar.favorite.isChecked()


def test_pink_theme_and_full_width_progress(window):
    assert TOKENS["background"] == "#F8D9E0"
    bar = window.playback_bar
    assert bar.seek.width() == bar.width()
    assert bar.seek.geometry().top() <= 2  # Allow the styled frame's top border.
    assert bar.buttons["Play"].text() == ""
    assert bar.buttons["Play"].accessibleName() == "Play"
