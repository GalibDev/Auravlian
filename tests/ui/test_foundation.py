import hashlib
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QPushButton

from auravlian.presentation.main_window import MainWindow
from auravlian.presentation.pages.settings import SettingsPage
from auravlian.presentation.theme.tokens import stylesheet
from auravlian.presentation.widgets.sidebar import PAGES
from auravlian.shared.paths import asset_path


def test_startup(window):
    assert window.isVisible()
    assert window.stack.count() == len(PAGES)
    assert window.sidebar.buttons["Home"].isChecked()
    assert window.playback_bar.isVisible()


@pytest.mark.parametrize("page", PAGES)
def test_navigation(window, qtbot, page):
    bar = window.playback_bar
    signal = QSignalSpy(window.container.events.page_changed)
    qtbot.mouseClick(window.sidebar.buttons[page], Qt.MouseButton.LeftButton)
    assert signal.count() == 1
    assert signal.at(0) == [page]
    assert window.stack.currentIndex() == PAGES.index(page)
    assert window.playback_bar is bar
    assert bar.isVisible()


def test_future_playback_is_disabled(window):
    controls = window.playback_bar.findChildren(QPushButton)
    assert len(controls) == 5
    assert all(not control.isEnabled() for control in controls)


def test_settings_survive_new_settings_instance(window, qtbot, container):
    window.navigate("Settings")
    page = window.pages["Settings"]
    assert isinstance(page, SettingsPage)
    qtbot.mouseClick(page.remember, Qt.MouseButton.LeftButton,
                     pos=QPoint(9, page.remember.height() // 2))
    reread = QSettings(container.settings.fileName(), QSettings.Format.IniFormat)
    assert reread.value("startup/remember_page", True, type=bool) is False


def test_page_and_geometry_restore(window, qtbot, container):
    window.navigate("Albums")
    window.close()
    restored = MainWindow(container)
    qtbot.addWidget(restored)
    assert restored.stack.currentIndex() == PAGES.index("Albums")
    assert container.settings.contains("window/geometry")


def test_disabled_restore_starts_at_home(qtbot, container):
    container.settings.setValue("window/page", "Albums")
    container.settings.setValue("startup/remember_page", False)
    window = MainWindow(container)
    qtbot.addWidget(window)
    assert window.stack.currentIndex() == 0


def test_invalid_page_falls_back(qtbot, container):
    container.settings.setValue("window/page", "removed-page")
    window = MainWindow(container)
    qtbot.addWidget(window)
    assert window.stack.currentIndex() == 0
    window.navigate("invalid")
    assert window.stack.currentIndex() == 0


def test_original_branding_is_byte_identical():
    original = Path(__file__).resolve().parents[2] / "assets/logo/original.png"
    assert hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(
        asset_path("logo", "original.png").read_bytes()).digest()
    assert "@" not in stylesheet()


def test_minimum_size_navigation(window, qtbot):
    window.resize(960, 700)
    qtbot.wait(50)
    assert window.sidebar.buttons["Settings"].isVisible()
    assert window.sidebar.buttons["Settings"].geometry().bottom() < window.sidebar.height()
    assert window.playback_bar.width() <= window.width()

