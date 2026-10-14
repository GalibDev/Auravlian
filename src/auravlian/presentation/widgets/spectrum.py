import numpy as np
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from auravlian.presentation.theme.tokens import TOKENS


class SpectrumWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(85)
        self.values = np.zeros(32)
        self.available = False
        self.setAccessibleName("Live decoded audio spectrum")

    def set_values(self, values) -> None:
        self.values = values
        self.available = True
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(QColor(TOKENS["muted"]))
        if not self.available:
            painter.drawText(8, 30, "Spectrum unavailable until this backend supplies decoded audio.")
            return
        width = self.width() / len(self.values)
        for index, value in enumerate(self.values):
            height = int(float(value) * (self.height() - 8))
            painter.fillRect(int(index * width), self.height() - height, max(1, int(width) - 4),
                             height, QColor(TOKENS["violet"] if index < 16 else TOKENS["cyan"]))
