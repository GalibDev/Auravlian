"""Application-owned dependencies, kept outside visual components."""
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QSettings, QThread

from auravlian.application.playback_service import PlaybackService
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.presentation.viewmodels.player_vm import PlayerViewModel
from auravlian.application.library_service import LibraryService
from auravlian.infrastructure.database.migrations import migrate
from auravlian.infrastructure.database.repositories.library_repository import LibraryRepository
from auravlian.infrastructure.filesystem.scanner import scan
from auravlian.infrastructure.cache.artwork_cache import ArtworkCache
from auravlian.infrastructure.metadata.mutagen_reader import read_track
from auravlian.presentation.viewmodels.library_vm import LibraryViewModel
from auravlian.shared.paths import data_path

from auravlian.shared.events import AppEvents
from auravlian.application.playlist_service import PlaylistService
from auravlian.infrastructure.database.repositories.collection_repository import CollectionRepository
from auravlian.presentation.viewmodels.playlist_vm import CollectionViewModel


@dataclass
class Container:
    settings: QSettings
    events: AppEvents
    _player: PlayerViewModel | None = field(default=None, init=False, repr=False)
    _saved_audio: tuple[int, bool] | None = field(default=None, init=False, repr=False)
    _library: LibraryViewModel | None = field(default=None, init=False, repr=False)
    _collections: CollectionViewModel | None = field(default=None, init=False, repr=False)

    @property
    def collections(self) -> CollectionViewModel:
        if self._collections is None:
            library = self.library
            repository = library.service.repository
            assert isinstance(repository, LibraryRepository)
            service = PlaylistService(CollectionRepository(repository.database),
                                      partial(migrate, repository.database), QCoreApplication.instance())
            self._collections = CollectionViewModel(service, library, QCoreApplication.instance())
            self.player.service.track_started.connect(service.record)
            app = QCoreApplication.instance()
            if app is not None:
                app.aboutToQuit.connect(service.shutdown)
            service.refresh()
        return self._collections

    @property
    def library(self) -> LibraryViewModel:
        if self._library is None:
            app = QCoreApplication.instance()
            if app is None or QThread.currentThread() != app.thread():
                raise RuntimeError("Create library dependencies on the application thread")
            # INI-based isolated sessions (tests/previews) keep all data alongside their INI.
            directory = (Path(self.settings.fileName()).parent / "library"
                         if self.settings.format() == QSettings.Format.IniFormat else data_path())
            repository = LibraryRepository(directory / "library.sqlite3")
            cache = ArtworkCache(directory / "artwork")
            service = LibraryService(repository, partial(migrate, repository.database), scan,
                                     partial(read_track, cache=cache), app)
            self._library = LibraryViewModel(service, self.player.service, app)
            app.aboutToQuit.connect(service.shutdown)
        return self._library

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
            device_id = str(self.settings.value("audio/device", ""))
            try:
                if device_id:
                    engine.select_device(bytes.fromhex(device_id))
            except ValueError:
                self.settings.setValue("audio/device", "")
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

