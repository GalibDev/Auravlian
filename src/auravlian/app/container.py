"""Application-owned dependencies, kept outside visual components."""
from dataclasses import dataclass

from PySide6.QtCore import QSettings

from auravlian.shared.events import AppEvents


@dataclass
class Container:
    settings: QSettings
    events: AppEvents

    @classmethod
    def create(cls) -> "Container":
        return cls(QSettings("Auravlian", "Auravlian"), AppEvents())

