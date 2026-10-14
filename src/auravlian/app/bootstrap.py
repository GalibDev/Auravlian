"""Native Qt application entry point."""
import json
import logging
import sys
import argparse
from pathlib import Path
from PySide6.QtCore import QSettings
from auravlian.shared.events import AppEvents

from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from auravlian.app.container import Container
from auravlian.app.lifecycle import configure_logging
from auravlian.presentation.main_window import MainWindow
from auravlian.presentation.theme.tokens import stylesheet
from auravlian.shared.paths import asset_path


def create_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setOrganizationName("Auravlian")
    app.setApplicationName("Auravlian")
    app.setApplicationVersion("0.8.0")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(QIcon(QPixmap(str(asset_path("logo", "original.png"))).copy(0, 0, 1254, 830)))
    app.setStyleSheet(stylesheet())
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="Auravlian local music player")
    parser.add_argument("--smoke-test", type=Path, help="Run isolated runtime diagnostics into this directory")
    parser.add_argument("files", nargs="*", help="Local audio files to open")
    arguments = parser.parse_args()
    app = create_application()
    configure_logging()
    logging.getLogger("auravlian").info(json.dumps("Application starting"))
    if arguments.smoke_test:
        directory = arguments.smoke_test.resolve()
        directory.mkdir(parents=True, exist_ok=True)
        container = Container(QSettings(str(directory / "settings.ini"), QSettings.Format.IniFormat), AppEvents())
    else:
        container = Container.create()
    window = MainWindow(container)
    window.show()
    if arguments.smoke_test:
        from auravlian.app.diagnostics import Diagnostics
        diagnostics = Diagnostics(window, directory)
        app.aboutToQuit.connect(diagnostics.timer.stop)
    elif arguments.files:
        container.player.service.open_files(arguments.files)
    return app.exec()

