"""Bounded real decoded-buffer spectrum. Never produces synthetic animation."""
import numpy as np
from PySide6.QtCore import QObject, QElapsedTimer, Signal, Slot
from PySide6.QtMultimedia import QAudioBuffer, QAudioFormat, QAudioBufferOutput, QMediaPlayer


def spectrum(samples: np.ndarray, sample_rate: int, bands: int = 32) -> np.ndarray:
    data = np.nan_to_num(np.asarray(samples, dtype=np.float32))[:4096]
    if data.size < 32 or sample_rate <= 0:
        return np.zeros(bands)
    fft = np.abs(np.fft.rfft(data * np.hanning(data.size))) / data.size
    frequencies = np.fft.rfftfreq(data.size, 1 / sample_rate)
    edges = np.geomspace(40, max(41, min(16000, sample_rate / 2)), bands + 1)
    values = []
    for low, high in zip(edges[:-1], edges[1:]):
        values_in_band = fft[(frequencies >= low) & (frequencies < high)]
        peak = float(values_in_band.max()) if values_in_band.size else 0
        values.append(np.clip((20 * np.log10(max(peak, 1e-9)) + 80) / 80, 0, 1))
    return np.asarray(values)


class AudioSpectrum(QObject):
    changed = Signal(object)

    def __init__(self, player: QMediaPlayer, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.player = player
        self.capture = QAudioBufferOutput(self)
        self.player.setAudioBufferOutput(self.capture)
        self.clock = QElapsedTimer()
        self.clock.start()
        self.capture.audioBufferReceived.connect(self.receive)
        player.playbackStateChanged.connect(self.state_changed)
        self.received = False

    @Slot(QMediaPlayer.PlaybackState)
    def state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state != QMediaPlayer.PlaybackState.PlayingState and self.received:
            self.changed.emit(np.zeros(32))

    @Slot(QAudioBuffer)
    def receive(self, buffer: QAudioBuffer) -> None:
        if not buffer.isValid() or self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return
        if self.clock.elapsed() < 50:
            return
        self.clock.restart()
        format_ = buffer.format()
        types = {QAudioFormat.SampleFormat.UInt8: (np.uint8, 128.0),
                 QAudioFormat.SampleFormat.Int16: (np.int16, 32768.0),
                 QAudioFormat.SampleFormat.Int32: (np.int32, 2147483648.0),
                 QAudioFormat.SampleFormat.Float: (np.float32, 1.0)}
        if format_.sampleFormat() not in types or format_.channelCount() < 1:
            return
        dtype, scale = types[format_.sampleFormat()]
        count = min(buffer.sampleCount(), 4096 * format_.channelCount())
        data = np.frombuffer(buffer.constData(), dtype=dtype, count=count).astype(np.float32)
        if dtype == np.uint8:
            data -= 128
        data = (data / scale).reshape(-1, format_.channelCount()).mean(axis=1)
        self.received = True
        self.changed.emit(spectrum(data, format_.sampleRate()))
