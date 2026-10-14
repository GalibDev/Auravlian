"""One Qt Multimedia player/output pair, used only on its Qt owning thread."""
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Signal, Slot, Qt
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer


class QtAudioEngine(QObject):
    state_changed = Signal(str)
    # PySide supports C++ type names at runtime; its stubs only declare Python types.
    position_changed = Signal("qlonglong")  # type: ignore[arg-type]
    duration_changed = Signal("qlonglong")  # type: ignore[arg-type]
    ready_changed = Signal(bool)
    seekable_changed = Signal(bool)
    ended = Signal()
    error = Signal(str)
    _play_requested = Signal()
    _pause_requested = Signal()
    _stop_requested = Signal()
    _source_requested = Signal(QUrl)
    _seek_requested = Signal("qlonglong")  # type: ignore[arg-type]

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        queued = Qt.ConnectionType.QueuedConnection
        self._play_requested.connect(self.player.play, queued)
        self._pause_requested.connect(self.player.pause, queued)
        self._stop_requested.connect(self.player.stop, queued)
        self._source_requested.connect(self.player.setSource, queued)
        self._seek_requested.connect(self.player.setPosition, queued)
        self.devices = QMediaDevices(self)
        self.devices.audioOutputsChanged.connect(self._devices_changed, Qt.ConnectionType.QueuedConnection)
        self._changing = False
        self._ended = False
        self._source = QUrl()
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.setInterval(15_000)
        self._load_timer.timeout.connect(self._load_timeout)
        self.player.playbackStateChanged.connect(self._state)
        self.player.mediaStatusChanged.connect(self._status)
        self.player.errorOccurred.connect(self._error)
        self.player.positionChanged.connect(self._position)
        self.player.durationChanged.connect(self._duration)
        self.player.seekableChanged.connect(self._seekable)

    def _check_thread(self) -> None:
        if QThread.currentThread() != self.thread():
            raise RuntimeError("Audio commands must run on the engine's owning Qt thread")

    def load(self, path: Path) -> None:
        self._check_thread()
        self._changing = True
        self._source = QUrl.fromLocalFile(str(path))
        self._ended = False
        self.ready_changed.emit(False)
        self.duration_changed.emit(0)
        self.position_changed.emit(0)
        self.seekable_changed.emit(False)
        self.state_changed.emit("loading")
        self._changing = False
        # Native queued slots avoid synchronous Python/backend teardown re-entry.
        # This resolves an observed immediate-stop hang and keeps source changes ordered.
        self.stop()
        self._source_requested.emit(QUrl())
        self._source_requested.emit(self._source)
        self._load_timer.start()
        self.play()

    def play(self) -> None:
        self._check_thread()
        if not QMediaDevices.audioOutputs():
            self._load_timer.stop()
            self.error.emit("No audio output device is available. Connect a device and try Play again.")
            return
        self._ended = False
        self._play_requested.emit()

    def pause(self) -> None:
        self._check_thread()
        self._pause_requested.emit()

    def stop(self) -> None:
        self._check_thread()
        self._load_timer.stop()
        self._stop_requested.emit()

    def seek(self, milliseconds: int) -> None:
        self._check_thread()
        if self.player.isSeekable():
            self._seek_requested.emit(max(0, min(milliseconds, self.player.duration())))

    def set_volume(self, percent: int) -> None:
        self._check_thread()
        self.output.setVolume(max(0, min(percent, 100)) / 100)

    def set_muted(self, muted: bool) -> None:
        self._check_thread()
        self.output.setMuted(muted)

    @Slot(QMediaPlayer.PlaybackState)
    def _state(self, state: QMediaPlayer.PlaybackState) -> None:
        if not self._changing and self.player.source() == self._source:
            self.state_changed.emit({
                QMediaPlayer.PlaybackState.PlayingState: "playing",
                QMediaPlayer.PlaybackState.PausedState: "paused",
                QMediaPlayer.PlaybackState.StoppedState: "stopped",
            }[state])

    @Slot(QMediaPlayer.MediaStatus)
    def _status(self, status: QMediaPlayer.MediaStatus) -> None:
        if self._changing or self.player.source() != self._source:
            return
        if status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.ready_changed.emit(False)
            self.state_changed.emit("loading")
        elif status in (QMediaPlayer.MediaStatus.LoadedMedia,
                         QMediaPlayer.MediaStatus.BufferedMedia):
            self._load_timer.stop()
            if not self.player.hasAudio():
                self.error.emit("This file has no playable audio stream.")
                return
            self.ready_changed.emit(True)
            if status == QMediaPlayer.MediaStatus.BufferedMedia:
                self._state(self.player.playbackState())
        elif status == QMediaPlayer.MediaStatus.EndOfMedia and not self._ended:
            self._ended = True
            self.ended.emit()
        elif status == QMediaPlayer.MediaStatus.StalledMedia:
            self._load_timer.start()
            self.state_changed.emit("buffering")

    @Slot(QMediaPlayer.Error, str)
    def _error(self, error: QMediaPlayer.Error, message: str) -> None:
        if (not self._changing and self.player.source() == self._source
                and error != QMediaPlayer.Error.NoError):
            self._load_timer.stop()
            self.ready_changed.emit(False)
            self.error.emit(message or "The file could not be decoded by the audio backend.")

    @Slot()
    def _load_timeout(self) -> None:
        self.stop()
        self.ready_changed.emit(False)
        self.error.emit("Audio loading timed out. Try the file again or choose another file.")

    @Slot("qlonglong")  # type: ignore[arg-type]
    def _position(self, value: int) -> None:
        if self.player.source() == self._source:
            self.position_changed.emit(value)

    @Slot("qlonglong")  # type: ignore[arg-type]
    def _duration(self, value: int) -> None:
        if self.player.source() == self._source:
            self.duration_changed.emit(value)

    @Slot(bool)
    def _seekable(self, value: bool) -> None:
        if self.player.source() == self._source:
            self.seekable_changed.emit(value)

    @Slot()
    def _devices_changed(self) -> None:
        if not QMediaDevices.audioOutputs():
            self.stop()
            self.error.emit("Audio output disconnected. Connect a device and try Play again.")
        else:
            self.output.setDevice(QMediaDevices.defaultAudioOutput())
