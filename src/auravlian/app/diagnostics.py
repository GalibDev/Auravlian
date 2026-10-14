"""Opt-in packaged-runtime smoke using isolated generated media and settings."""
import json
import math
from pathlib import Path
import struct
import traceback
import wave

from PySide6.QtCore import QObject, QTimer, QElapsedTimer

from auravlian.presentation.main_window import MainWindow
from auravlian.infrastructure.audio.qt_audio_engine import QtAudioEngine
from auravlian.presentation.pages.now_playing import NowPlayingPage


class Diagnostics(QObject):
    def __init__(self, window: MainWindow, directory: Path) -> None:
        super().__init__(window)
        self.window, self.directory = window, directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "diagnostic.wav"
        with wave.open(str(self.path), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(
                2 * math.pi * 440 * i / 16000))) for i in range(16000 * 5)))
        self.path.with_suffix(".lrc").write_text("[00:00.00]Local diagnostic tone\n[00:01.00]Decoded audio", encoding="utf-8")
        self.stage = 0
        self.started = QElapsedTimer()
        self.started.start()
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def finish(self, report: dict) -> None:
        self.timer.stop()
        (self.directory / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.window.grab().save(str(self.directory / "screenshot.png"))
        self.window.quit_application()

    def tick(self) -> None:
        container = self.window.container
        library = container.library.service
        collections = container.collections.service
        player = container.player.service
        try:
            if self.started.elapsed() > 20000:
                raise RuntimeError(f"Diagnostic timeout at stage {self.stage}: {player.error_message}")
            if self.stage == 0 and not library.busy and not collections.busy:
                library.start("import", [self.path])
                self.stage = 1
            elif self.stage == 1 and not library.busy:
                assert library.tracks, library.last_result.error
                player.set_muted(True)
                player.open_tracks(library.tracks)
                self.window.navigate("Now Playing")
                self.stage = 2
            elif self.stage == 2 and player.ready and player.position > 500:
                player.pause()
                self.stage = 3
            elif self.stage == 3 and player.state == "paused":
                player.seek(1500)
                self.stage = 4
            elif self.stage == 4 and abs(player.position - 1500) < 100 and not collections.busy:
                engine = player.audio
                assert isinstance(engine, QtAudioEngine)
                assert collections.snapshot.play_count >= 1
                now_playing = self.window.pages["Now Playing"]
                assert isinstance(now_playing, NowPlayingPage)
                report = {"result": "passed", "duration_ms": player.duration,
                          "paused_seek_ms": player.position, "imported_tracks": len(library.tracks),
                          "history_starts": collections.snapshot.play_count,
                          "decoded_buffer_capture": engine.spectrum.received,
                          "lyrics_lines": len(now_playing.lyrics.lines),
                          "version": "0.8.0"}
                self.finish(report)
        except Exception:
            self.finish({"result": "failed", "error": traceback.format_exc(), "stage": self.stage})
