"""Native Qt application entry point."""
import json
import logging
import sys

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
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(QIcon(QPixmap(str(asset_path("logo", "original.png"))).copy(0, 0, 1254, 830)))
    app.setStyleSheet(stylesheet())
    return app


def main() -> int:
    app = create_application()
    configure_logging()
    logging.getLogger("auravlian").info(json.dumps("Application starting"))
    window = MainWindow(Container.create())
    window.show()
    return app.exec()

