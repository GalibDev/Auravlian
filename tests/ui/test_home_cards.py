from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from auravlian.domain.models.track import Track
from auravlian.presentation.pages.home import HomePage
from auravlian.presentation.widgets.sidebar import PAGES


def test_home_cards_navigate(window, qtbot):
    home = window.pages["Home"]
    assert isinstance(home, HomePage)
    for page, card in home.cards.items():
        window.navigate("Home")
        qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
        assert window.stack.currentIndex() == PAGES.index(page)
        assert window.sidebar.buttons[page].isChecked()


def test_home_artwork_and_empty_fallback(qtbot, tmp_path):
    home = HomePage()
    qtbot.addWidget(home)
    cover = QPixmap(20, 20)
    cover.fill(Qt.GlobalColor.red)
    path = tmp_path / "cover.png"
    assert cover.save(str(path))
    home.set_artwork("Albums", [Track(Path("song.wav"), artwork_path=str(path))])
    assert not home.artworks["Albums"].icon().isNull()
    home.set_artwork("Albums", [Track(Path("song.wav"))])
    assert home.artworks["Albums"].icon().isNull()
    assert "Browse Albums" in home.artworks["Albums"].text()
    home.set_artwork("Albums", [])
    assert "No music yet" in home.artworks["Albums"].text()
