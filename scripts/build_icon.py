"""Crop the supplied original symbol and pad it; never redraw or recolor branding."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

source = QImage("assets/logo/original.png").copy(0, 0, 1254, 830)
symbol = source.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
canvas = QImage(256, 256, QImage.Format.Format_ARGB32)
canvas.fill(Qt.GlobalColor.transparent)
painter = QPainter(canvas)
painter.drawImage((256 - symbol.width()) // 2, (256 - symbol.height()) // 2, symbol)
painter.end()
assert canvas.save(str(Path("assets/logo/auravlian.ico")))
