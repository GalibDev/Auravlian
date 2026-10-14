from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QVBoxLayout, QWidget

from auravlian.presentation.pages.base import label


class SettingsPage(QWidget):
    def __init__(self, settings: QSettings) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)
        layout.addWidget(label("MAKE IT YOURS", "eyebrow"))
        layout.addWidget(label("Settings", "title"))
        layout.addWidget(label("Preferences are saved automatically on this computer.", "subtitle"))
        card = QFrame()
        card.setObjectName("card")
        body = QVBoxLayout(card)
        body.setContentsMargins(24, 24, 24, 24)
        body.addWidget(label("Startup", "section"))
        self.remember = QCheckBox("Restore the last page when Auravlian opens")
        self.remember.setChecked(bool(settings.value("startup/remember_page", True, type=bool)))
        self.remember.checkStateChanged.connect(
            lambda state: self.save(settings, state == Qt.CheckState.Checked))
        body.addWidget(self.remember)
        body.addWidget(label("Appearance · Aurora dark\nAudio settings arrive with playback.",
                             "subtitle"))
        layout.addWidget(card)
        layout.addStretch()
        layout.addWidget(label("Auravlian 0.1.0 · Phase 1\nFeel Beyond Sound.", "subtitle"))

    @staticmethod
    def save(settings: QSettings, checked: bool) -> None:
        settings.setValue("startup/remember_page", checked)
        settings.sync()

