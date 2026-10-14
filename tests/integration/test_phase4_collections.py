from pathlib import Path
import wave

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtMultimedia import QMediaDevices

from auravlian.application.playlist_service import PlaylistService
from auravlian.application.playback_service import PlaybackService
from auravlian.domain.models.track import Track
from auravlian.domain.playback.queue import PlaybackQueue
from auravlian.infrastructure.database.connection import connection
from auravlian.infrastructure.database.migrations import migrate, SCHEMA
from auravlian.infrastructure.database.repositories.library_repository import LibraryRepository
from auravlian.infrastructure.database.repositories.collection_repository import CollectionRepository


@pytest.fixture
def collection(tmp_path):
    database = tmp_path / "collections.db"
    migrate(database)
    library = LibraryRepository(database)
    tracks = [Track(tmp_path / f"{i}.wav", f"Song {i}", "Artist", "Album", 1000) for i in range(3)]
    library.upsert(tracks)
    return CollectionRepository(database), library, tracks


def test_phase4_upgrade_preserves_existing_library(tmp_path):
    database = tmp_path / "v1.db"
    with connection(database) as db:
        for sql in SCHEMA:
            db.execute(sql)
        db.execute("PRAGMA user_version=1")
    library = LibraryRepository(database)
    library.upsert([Track(tmp_path / "kept.wav")])
    migrate(database)
    migrate(database)
    assert library.tracks()[0].title == "kept"
    with connection(database) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2


def test_phase4_playlist_crud_dedup_and_order(collection):
    repo, _, tracks = collection
    repo.create("  Evening  ")
    playlist = repo.snapshot().playlists[0]
    assert playlist.name == "Evening"
    repo.add(playlist.id, [t.path for t in tracks] + [tracks[0].path])
    assert [t.title for t in repo.snapshot().playlists[0].tracks] == ["Song 0", "Song 1", "Song 2"]
    repo.reorder(playlist.id, [t.path for t in reversed(tracks)])
    assert repo.snapshot().playlists[0].tracks[0].title == "Song 2"
    repo.remove(playlist.id, [tracks[1].path])
    repo.rename(playlist.id, "Night")
    assert repo.snapshot().playlists[0].name == "Night"
    assert len(repo.snapshot().playlists[0].tracks) == 2
    repo.delete(playlist.id)
    assert repo.snapshot().playlists == []
    assert len(repo.snapshot().favorites) == 0


def test_phase4_validation_and_atomic_add(collection):
    repo, _, tracks = collection
    with pytest.raises(ValueError):
        repo.create(" ")
    repo.create("Mix")
    with pytest.raises(ValueError, match="already"):
        repo.create("mix")
    playlist_id = repo.snapshot().playlists[0].id
    with pytest.raises(ValueError, match="Import"):
        repo.add(playlist_id, [tracks[0].path, Path("not-imported.wav")])
    assert repo.snapshot().playlists[0].tracks == ()
    repo.add(playlist_id, [t.path for t in tracks])
    with pytest.raises(ValueError, match="changed"):
        repo.reorder(playlist_id, [tracks[0].path])
    assert len(repo.snapshot().playlists[0].tracks) == 3


def test_phase4_favorites_and_rescan_preserve_membership(collection):
    repo, library, tracks = collection
    repo.create("Keep")
    playlist_id = repo.snapshot().playlists[0].id
    repo.add(playlist_id, [tracks[0].path])
    repo.favorite([tracks[0].path], True)
    repo.favorite([tracks[0].path], True)
    library.upsert([Track(tracks[0].path, "Updated", "Artist", "Album", 2000)])
    library.mark_missing(tracks[0].path, True)
    snapshot = repo.snapshot()
    assert snapshot.favorites[0].title == "Updated"
    assert snapshot.favorites[0].missing
    assert snapshot.playlists[0].tracks[0].missing
    repo.favorite([tracks[0].path], False)
    assert repo.snapshot().favorites == []


def test_phase4_recent_unique_history_and_direct_files(collection):
    repo, _, tracks = collection
    repo.record_play(tracks[0])
    repo.record_play(tracks[1])
    repo.record_play(tracks[0])
    direct = Track(Path("direct-file.wav"), "Direct")
    repo.record_play(direct)
    snapshot = repo.snapshot()
    assert snapshot.play_count == 4
    assert [t.title for t in snapshot.history] == ["Direct", "Song 0", "Song 1"]
    assert CollectionRepository(repo.database).snapshot().play_count == 4


def test_phase4_background_service_queue_and_error_recovery(qapp, qtbot, collection):
    repo, _, tracks = collection
    service = PlaylistService(repo, lambda: migrate(repo.database))
    try:
        service.create("First")
        service.create("Second")
        qtbot.waitUntil(lambda: not service.busy)
        assert len(service.snapshot.playlists) == 2
        service.create("First")
        qtbot.waitUntil(lambda: not service.busy)
        assert "already" in service.error
        service.favorite([tracks[0].path], True)
        qtbot.waitUntil(lambda: not service.busy)
        assert service.error == "" and len(service.snapshot.favorites) == 1
    finally:
        service.shutdown()


def test_phase4_start_signal_waits_for_decoding_and_ignores_resume(qapp, tmp_path):
    class Audio:
        def load(self, path): pass
        def play(self): pass
        def pause(self): pass
        def stop(self): pass
        def seek(self, value): pass
        def set_volume(self, value): pass
        def set_muted(self, value): pass

    path = tmp_path / "valid.wav"
    path.touch()
    service = PlaybackService(Audio(), PlaybackQueue())
    starts = QSignalSpy(service.track_started)
    service.open_files([path])
    service.on_state("playing")
    assert starts.count() == 0
    service.on_ready(True)
    assert starts.count() == 1
    service.on_state("paused")
    service.on_state("playing")
    assert starts.count() == 1
    service.stop()
    service.on_state("playing")
    assert starts.count() == 2
    service.shutdown()


def test_phase4_real_playback_records_once_per_start(qapp, qtbot, container, tmp_path):
    if not QMediaDevices.audioOutputs():
        pytest.skip("Physical output device required for real Qt playback history test")
    path = tmp_path / "actual-history.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 8000 * 3)
    collections = container.collections.service
    player = container.player.service
    player.set_muted(True)
    qtbot.waitUntil(lambda: not collections.busy)
    try:
        player.open_tracks([Track(path, "Actual history")])
        qtbot.waitUntil(lambda: collections.snapshot.play_count == 1, timeout=10_000)
        player.pause()
        qtbot.waitUntil(lambda: player.state == "paused")
        player.play()
        qtbot.waitUntil(lambda: player.state == "playing")
        assert collections.snapshot.play_count == 1
        assert collections.snapshot.history[0].title == "Actual history"
    finally:
        player.stop()
        collections.shutdown()
