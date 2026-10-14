"""Content-addressed thumbnails; QImage is safe to use in scanner workers."""
import hashlib
from pathlib import Path

from PySide6.QtCore import Qt, QSaveFile, QIODevice
from PySide6.QtGui import QImage


class ArtworkCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def store(self, data: bytes) -> str:
        if len(data) > 20_000_000:
            return ""
        target = self.directory / (hashlib.sha256(data).hexdigest() + ".png")
        if target.is_file():
            return str(target)
        image = QImage.fromData(data)
        if image.isNull():
            return ""
        self.directory.mkdir(parents=True, exist_ok=True)
        thumbnail = image.scaled(192, 192, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
        output = QSaveFile(str(target))
        if not output.open(QIODevice.OpenModeFlag.WriteOnly):
            raise OSError(output.errorString())
        # PySide 6.8 accepts str here at runtime despite its bytes-only stub.
        if not thumbnail.save(output, "PNG") or not output.commit():  # type: ignore[call-overload]
            raise OSError("Could not save artwork thumbnail")
        return str(target)
