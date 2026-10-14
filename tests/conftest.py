import pytest
from PySide6.QtCore import QSettings

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.presentation.main_window import MainWindow
from auravlian.shared.events import AppEvents


@pytest.fixture(scope="session")
def qapp():
    return create_application([])


@pytest.fixture
def container(tmp_path):
    return Container(QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat), AppEvents())


@pytest.fixture
def window(qtbot, container):
    widget = MainWindow(container)
    qtbot.addWidget(widget)
    widget.show()
    return widget

