"""Render real Qt widgets for repeatable visual inspection without changing user settings."""
from pathlib import Path

from PySide6.QtCore import QSettings

from auravlian.app.bootstrap import create_application
from auravlian.app.container import Container
from auravlian.presentation.main_window import MainWindow
from auravlian.shared.events import AppEvents

app = create_application([])
output = Path("artifacts")
output.mkdir(exist_ok=True)
settings = QSettings(str(output.resolve() / "preview.ini"), QSettings.Format.IniFormat)
settings.clear()
window = MainWindow(Container(settings, AppEvents()))
window.show()
for name in ("Home", "Library", "Settings"):
    window.navigate(name)
    app.processEvents()
    window.grab().save(str(output / f"{name.lower()}.png"))
window.resize(960, 700)
window.navigate("Home")
app.processEvents()
window.grab().save(str(output / "home-small.png"))
window.close()

