from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


def label(text: str, role: str) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setObjectName(role)
    widget.setWordWrap(True)
    return widget


class EmptyPage(QWidget):
    def __init__(self, title: str, subtitle: str, empty: str, detail: str, phase: int) -> None:
        super().__init__()
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(36, 30, 36, 30)
        self.layout_.setSpacing(16)
        self.layout_.addWidget(label("YOUR MUSIC, YOUR WORLD", "eyebrow"))
        self.layout_.addWidget(label(title, "title"))
        self.layout_.addWidget(label(subtitle, "subtitle"))
        card = QFrame()
        card.setObjectName("card")
        body = QVBoxLayout(card)
        body.setContentsMargins(32, 48, 32, 48)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(label(empty, "section"))
        body.addWidget(label(detail, "subtitle"))
        button = QPushButton(f"Available in Phase {phase}")
        button.setEnabled(False)
        body.addWidget(button)
        self.layout_.addWidget(card, 1)

