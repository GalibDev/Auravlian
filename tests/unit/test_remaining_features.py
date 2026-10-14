from pathlib import Path

import numpy as np
import pytest

from auravlian.domain.models.track import Track
from auravlian.domain.playback.lyrics import parse_lrc, current_line
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.infrastructure.audio.visualizer import spectrum
from auravlian.application.playlist_io import read_m3u, write_m3u
from auravlian.application.lyrics_service import LyricsService


def test_lrc_offsets_multiple_timestamps_and_malformed_lines():
    lines = parse_lrc("[ar:Artist]\n[offset:-100]\n[00:01.5][00:03.050]Hello\n[01:02]Later\n[99:no]Bad")
    assert [(line.milliseconds, line.text) for line in lines] == [(1400, "Hello"), (2950, "Hello"), (61900, "Later")]
    assert current_line(lines, 0) == -1
    assert current_line(lines, 2000) == 0
    assert current_line(lines, 99999) == 2
    assert parse_lrc("untimed text") == []


def test_queue_select_remove_and_empty():
    tracks = [Track(Path(f"{i}.wav")) for i in range(3)]
    queue = PlaybackQueue()
    queue.replace(tracks)
    assert queue.select(1) == tracks[1]
    queue.remove(0)
    assert queue.current == tracks[1]
    queue.remove(0)
    assert queue.current == tracks[2]
    queue.remove(0)
    assert queue.current is None
    assert queue.select(100) is None
    queue.remove(-1)


def test_spectrum_silence_and_known_frequency():
    rate = 16000
    tone = np.sin(2 * np.pi * 1000 * np.arange(4096) / rate)
    silent = spectrum(np.zeros(4096), rate)
    levels = spectrum(tone, rate)
    assert np.all(silent == 0)
    assert levels.max() > 0.7
    edges = np.geomspace(40, 8000, 33)
    peak = int(levels.argmax())
    assert edges[peak] < 1000 < edges[peak + 1]
    assert np.isfinite(spectrum(np.full(4096, np.nan), rate)).all()
    assert np.all(spectrum(np.zeros(4), rate) == 0)


def test_m3u_relative_paths_round_trip_and_remote_rejection(tmp_path):
    path = tmp_path / "mix.m3u8"
    path.write_text("#EXTM3U\nlocal.wav\n#EXTINF:5,Title\nsub/music.flac\n", encoding="utf-8")
    assert read_m3u(path) == [tmp_path / "local.wav", tmp_path / "sub/music.flac"]
    tracks = (Track(tmp_path / "local.wav", "Title", duration_ms=5000),)
    write_m3u(path, tracks)
    assert read_m3u(path) == [tracks[0].path]
    path.write_text("https://example.com/audio.mp3")
    with pytest.raises(ValueError, match="local"):
        read_m3u(path)


def test_background_lyrics_latest_track_wins(qapp, qtbot, tmp_path):
    first, second = tmp_path / "first.wav", tmp_path / "second.wav"
    first.with_suffix(".lrc").write_text("[00:00.0]Old lyrics", encoding="utf-8")
    second.with_suffix(".lrc").write_text("[00:00.0]Current lyrics", encoding="utf-8")
    service = LyricsService()
    try:
        service.load(first)
        service.load(second)
        qtbot.waitUntil(lambda: not service.jobs)
        assert service.lines[0].text == "Current lyrics"
        service.load(tmp_path / "missing.wav")
        qtbot.waitUntil(lambda: not service.jobs)
        assert not service.lines and "No local" in service.status
    finally:
        service.shutdown()
