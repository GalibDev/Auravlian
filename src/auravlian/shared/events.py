"""Application-wide events; playback signals belong to the future audio adapter."""
from PySide6.QtCore import QObject, Signal


class AppEvents(QObject):
    page_changed = Signal(str)

