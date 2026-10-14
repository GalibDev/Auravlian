"""Read-only package assets and per-user writable paths."""
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def asset_path(*parts: str) -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / Path(*parts)


def data_path() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path

