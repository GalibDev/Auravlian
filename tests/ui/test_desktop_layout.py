from pathlib import Path

from PySide6.QtCore import Qt

from auravlian.domain.models.track import Track
from auravlian.presentation.pages.home import HomePage
from auravlian.presentation.widgets.music_card import MusicCard
from auravlian.presentation.widgets.sidebar import PAGES


def test_global_search_filters_library(window, qtbot):
    qtbot.keyClicks(window.global_search, "Aurora")
    assert window.stack.currentIndex() == PAGES.index("Library")
    assert window.pages["Library"].search.text() == "Aurora"


def test_queue_toggle_persists_without_replacing_engine(window, qtbot):
    engine = window.player_vm.service.audio
    qtbot.mouseClick(window.queue_toggle, Qt.MouseButton.LeftButton)
    assert not window.queue_panel.isVisible()
    assert window.container.settings.value("window/queue_visible", type=bool) is False
    window.show_queue()
    assert window.queue_panel.isVisible()
    assert not window.queue_panel.isWindow()
    assert window.queue_panel.vm.service.audio is engine


def test_home_music_card_plays_selected_track(window, qtbot, monkeypatch):
    home = window.pages["Home"]
    assert isinstance(home, HomePage)
    track = Track(Path("sample.wav"), "Local sample", "Test artist")
    window.container.library.service.tracks = [track]
    played = []
    monkeypatch.setattr(window.container.library, "play", lambda tracks: played.extend(tracks))
    home.refresh_library()
    card = home.findChild(MusicCard)
    assert card is not None
    qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
    assert played == [track]


def test_missing_music_card_is_disabled(qtbot):
    card = MusicCard(Track(Path("gone.mp3"), missing=True))
    qtbot.addWidget(card)
    assert not card.isEnabled()
