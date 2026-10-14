import sqlite3
from pathlib import Path
from threading import Event, get_ident
import wave

import pytest
from mutagen.wave import WAVE
from mutagen.id3 import TIT2, TPE1, TALB, APIC
from PySide6.QtCore import QBuffer, QIODevice, QTimer, Qt
from PySide6.QtGui import QImage

from auravlian.application.library_service import LibraryService
from auravlian.domain.models.track import Track
from auravlian.infrastructure.database.connection import connection
from auravlian.infrastructure.database.migrations import migrate
from auravlian.infrastructure.database.repositories.library_repository import LibraryRepository
from auravlian.infrastructure.cache.artwork_cache import ArtworkCache
from auravlian.infrastructure.filesystem.scanner import scan
from auravlian.infrastructure.metadata.mutagen_reader import read_track


def wav(path, tagged=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8000)
        stream.writeframes(b"\x00\x00" * 8000)
    if tagged:
        audio = WAVE(path)
        audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text="Aurora"))
        audio.tags.add(TPE1(encoding=3, text="Test Artist"))
        audio.tags.add(TALB(encoding=3, text="Test Album"))
        audio.save()
    return path


def finish(qtbot, service):
    qtbot.waitUntil(lambda: not service.busy, timeout=10_000)
    assert not service.last_result.error


def test_migrations_idempotent_and_reject_future(tmp_path):
    path = tmp_path / "library.db"
    migrate(path)
    migrate(path)
    with connection(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="newer"):
        migrate(path)


def test_repository_dedup_normalization_and_identity(tmp_path):
    path = tmp_path / "library.db"
    migrate(path)
    repo = LibraryRepository(path)
    media = wav(tmp_path / "music.wav")
    assert repo.upsert([Track(media), Track(media.parent / "." / media.name)]) == 1
    with connection(path) as db:
        original = db.execute("SELECT id,added_at FROM tracks").fetchone()
        db.execute("CREATE TABLE retained_reference(track_id REFERENCES tracks(id))")
        db.execute("INSERT INTO retained_reference VALUES(?)", (original[0],))
    assert repo.upsert([Track(media, "Changed", "Artist", "Album", 1234)]) == 0
    assert repo.tracks()[0].title == "Changed"
    with connection(path) as db:
        assert tuple(db.execute("SELECT id,added_at FROM tracks").fetchone()) == tuple(original)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("SELECT count(*) FROM retained_reference").fetchone()[0] == 1


def test_repository_batch_failure_rolls_back(tmp_path):
    path = tmp_path / "library.db"
    migrate(path)
    repo = LibraryRepository(path)
    with pytest.raises((TypeError, sqlite3.Error)):
        repo.upsert([Track(tmp_path / "good.wav"), Track(tmp_path / "bad.wav", artist=None)])
    assert repo.tracks() == []


def test_metadata_tags_and_untagged_fallback(tmp_path):
    cache = ArtworkCache(tmp_path / "cache")
    track = read_track(wav(tmp_path / "tagged.wav", tagged=True), cache)
    assert (track.title, track.artist, track.album, track.duration_ms) == (
        "Aurora", "Test Artist", "Test Album", 1000)
    fallback = read_track(wav(tmp_path / "fallback.wav"), cache)
    assert fallback.title == "fallback"
    assert fallback.artist == "Unknown artist" and fallback.artwork_path == ""
    invalid = tmp_path / "bad.mp3"
    invalid.write_bytes(b"corrupt")
    with pytest.raises(Exception):
        read_track(invalid, cache)


def test_artwork_extraction_cache_and_invalid_cover(qapp, tmp_path):
    media = wav(tmp_path / "cover.wav", tagged=True)
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.cyan)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    data = bytes(buffer.data())
    audio = WAVE(media)
    audio.tags.add(APIC(encoding=3, mime="image/png", type=3, data=data))
    audio.save()
    cache = ArtworkCache(tmp_path / "cache")
    track = read_track(media, cache)
    assert Path(track.artwork_path).is_file()
    thumb = QImage(track.artwork_path)
    assert (thumb.width(), thumb.height()) == (192, 96)
    assert cache.store(data) == track.artwork_path
    assert cache.store(b"not an image") == ""
    assert len(list(cache.directory.iterdir())) == 1


def test_scanner_recursive_duplicates_case_and_cancel(tmp_path):
    first = wav(tmp_path / "nested" / "music.WAV")
    (tmp_path / "notes.txt").write_text("ignore")
    warnings = []
    cancel = Event()
    assert list(scan([tmp_path, first], cancel, warnings.append)) == [first]
    assert not warnings
    cancel.set()
    assert list(scan([tmp_path], cancel, warnings.append)) == []
    cancel.clear()
    list(scan([tmp_path / "missing"], cancel, warnings.append))
    assert warnings


def test_background_import_rescan_restore_and_reopen(qapp, qtbot, container, tmp_path):
    service = container.library.service
    folder = tmp_path / "music"
    first = wav(folder / "one.wav", tagged=True)
    wav(folder / "sub" / "two.wav")
    (folder / "bad.mp3").write_bytes(b"bad")
    assert service.start("import", [folder, first])
    assert not service.start("import", [folder])
    finish(qtbot, service)
    assert len(service.tracks) == 2 and service.last_result.added == 2
    assert service.last_result.warnings
    assert service.repository.folders() == [folder.resolve()]
    assert service.start("import", [folder])
    finish(qtbot, service)
    assert service.last_result.added == 0
    first.unlink()
    third = wav(folder / "three.wav")
    service.start("rescan")
    finish(qtbot, service)
    assert len(service.tracks) == 3
    assert sum(track.missing for track in service.tracks) == 1
    wav(first, tagged=True)
    service.start("rescan")
    finish(qtbot, service)
    assert not any(track.missing for track in service.tracks)
    assert any(track.path == third.resolve() for track in service.tracks)
    # A new connection/repository sees persisted state after the worker has finished.
    repository = service.repository
    assert isinstance(repository, LibraryRepository)
    assert len(LibraryRepository(repository.database).tracks()) == 3


def test_worker_responsiveness_thread_ownership_and_cancel(qapp, qtbot, tmp_path):
    database = tmp_path / "library.db"
    repo = LibraryRepository(database)
    media = wav(tmp_path / "slow.wav")
    entered, release = Event(), Event()
    threads = []

    def reader(path):
        threads.append(get_ident())
        entered.set()
        assert release.wait(5)
        return Track(path)

    service = LibraryService(repo, lambda: migrate(database), scan, reader)
    ticks = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    try:
        service.start("import", [media])
        qtbot.waitUntil(entered.is_set)
        qtbot.waitUntil(lambda: len(ticks) >= 3)
        assert threads[0] != get_ident()
        service.cancel()
        release.set()
        finish(qtbot, service)
        assert service.last_result.cancelled
    finally:
        release.set()
        timer.stop()
        service.shutdown()


def test_worker_error_is_visible_without_crash(qapp, qtbot, tmp_path):
    def fail():
        raise OSError("read-only database directory")

    service = LibraryService(LibraryRepository(tmp_path / "db"), fail, scan, lambda p: Track(p))
    service.start()
    qtbot.waitUntil(lambda: not service.busy)
    assert "read-only" in service.status
    service.shutdown()
