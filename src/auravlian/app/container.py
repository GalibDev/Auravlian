"""Application-owned dependencies, kept outside visual components."""
from dataclasses import dataclass, field

from PySide6.QtCore import QCoreApplication, QSettings, QThread

from auravlian.application.playback_service import PlaybackService
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel

from auravlian.shared.events import AppEvents


@dataclass
class Container:
    settings: QSettings
    events: AppEvents
    _player: PlayerViewModel | None = field(default=None, init=False, repr=False)
    _saved_audio: tuple[int, bool] | None = field(default=None, init=False, repr=False)

    @property
    def player(self) -> PlayerViewModel:
        if self._player is None:
            app = QCoreApplication.instance()
            if app is None:
                raise RuntimeError("Create the Qt application before playback dependencies")
            if QThread.currentThread() != app.thread():
                raise RuntimeError("Playback dependencies must be created on the application thread")
            engine = QtAudioEngine(app)
            service = PlaybackService(engine, PlaybackQueue(), app)
            engine.state_changed.connect(service.on_state)
            engine.position_changed.connect(service.on_position)
            engine.duration_changed.connect(service.on_duration)
            engine.ready_changed.connect(service.on_ready)
            engine.seekable_changed.connect(service.on_seekable)
            engine.ended.connect(service.on_ended)
            engine.error.connect(service.on_error)
            try:
                volume = int(str(self.settings.value("audio/volume", 70)))
            except (ValueError, TypeError):
                volume = 70
            service.set_volume(volume)
            service.set_muted(bool(self.settings.value("audio/muted", False, type=bool)))
            self._player = PlayerViewModel(service, app)
            service.changed.connect(self._save_audio_settings)
            app.aboutToQuit.connect(service.shutdown)
            app.aboutToQuit.connect(self.settings.sync)
        return self._player

    def _save_audio_settings(self) -> None:
        if self._player is not None:
            service = self._player.service
            values = (service.volume, service.muted)
            if values != self._saved_audio:
                self.settings.setValue("audio/volume", service.volume)
                self.settings.setValue("audio/muted", service.muted)
                self._saved_audio = values

    @classmethod
    def create(cls) -> "Container":
        return cls(QSettings("Auravlian", "Auravlian"), AppEvents())

