from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QVBoxLayout, QWidget, QComboBox
from PySide6.QtMultimedia import QMediaDevices
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine

from auravlian.presentation.pages.base import label


class SettingsPage(QWidget):
    def __init__(self, settings: QSettings, engine: QtAudioEngine | None = None) -> None:
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
        self.tray = QCheckBox("Keep playing in the system tray when closing the window")
        self.tray.setChecked(bool(settings.value("desktop/tray", False, type=bool)))
        self.tray.toggled.connect(lambda checked: settings.setValue("desktop/tray", checked))
        body.addWidget(self.tray)
        body.addWidget(label("Audio output", "section"))
        self.devices = QComboBox()
        self.devices.setAccessibleName("Audio output device")
        body.addWidget(self.devices)
        self.engine = engine
        self.settings = settings
        self.populate_devices()
        if engine is not None:
            engine.devices.audioOutputsChanged.connect(self.populate_devices)
            self.devices.currentIndexChanged.connect(self.choose_device)
        else:
            self.devices.setEnabled(False)
        body.addWidget(label("Appearance · Aurora dark\nSpectrum uses actual decoded audio buffers.", "subtitle"))
        layout.addWidget(card)
        layout.addStretch()
        layout.addWidget(label("Auravlian 0.8.0\nFeel Beyond Sound.", "subtitle"))

    def populate_devices(self) -> None:
        self.devices.blockSignals(True)
        self.devices.clear()
        self.devices.addItem("Windows default output", "")
        selected = str(self.settings.value("audio/device", ""))
        for device in QMediaDevices.audioOutputs():
            key = device.id().data().hex()
            self.devices.addItem(device.description(), key)
            if key == selected:
                self.devices.setCurrentIndex(self.devices.count() - 1)
        self.devices.blockSignals(False)

    def choose_device(self, index: int) -> None:
        key = str(self.devices.itemData(index) or "")
        self.settings.setValue("audio/device", key)
        if self.engine is not None:
            self.engine.select_device(bytes.fromhex(key))

    @staticmethod
    def save(settings: QSettings, checked: bool) -> None:
        settings.setValue("startup/remember_page", checked)
        settings.sync()

