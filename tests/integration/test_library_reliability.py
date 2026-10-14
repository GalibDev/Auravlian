from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

from auravlian.application.library_service import LibraryService
from auravlian.domain.models.track import Track
from auravlian.infrastructure.database.connection import connection
from auravlian.infrastructure.database.migrations import migrate
from auravlian.infrastructure.database.repositories.library_repository import LibraryRepository
from auravlian.infrastructure.filesystem.scanner import scan


def test_concurrent_migration_and_thread_owned_connections(tmp_path):
    database = tmp_path / "library.db"
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: migrate(database), range(2)))
        list(pool.map(lambda i: LibraryRepository(database).upsert([
            Track(tmp_path / f"{i}.wav")]), range(20)))
    assert len(LibraryRepository(database).tracks()) == 20
    with connection(database) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_cancelled_rescan_preserves_missing_flags(qapp, qtbot, tmp_path):
    database = tmp_path / "library.db"
    migrate(database)
    repo = LibraryRepository(database)
    missing = tmp_path / "gone.wav"
    repo.upsert([Track(missing)])
    entered, release = Event(), Event()

    def scanner(paths, cancelled, warning):
        entered.set()
        assert release.wait(5)
        return iter(())

    service = LibraryService(repo, lambda: migrate(database), scanner, lambda p: Track(p))
    try:
        service.start("rescan")
        qtbot.waitUntil(entered.is_set)
        service.cancel()
        release.set()
        qtbot.waitUntil(lambda: not service.busy)
        assert service.last_result.cancelled
        assert repo.tracks()[0].missing is False
    finally:
        release.set()
        service.shutdown()


def test_warning_details_bounded_but_count_complete(qapp, qtbot, tmp_path):
    database = tmp_path / "library.db"

    def scanner(paths, cancelled, warning):
        for i in range(120):
            warning(f"Skipped unavailable input {i}")
        return iter(())

    service = LibraryService(LibraryRepository(database), lambda: migrate(database),
                             scanner, lambda p: Track(p))
    service.start("import", [Path("missing")])
    qtbot.waitUntil(lambda: not service.busy)
    assert len(service.last_result.warnings) == 100
    assert service.last_result.warning_count == 120
    service.shutdown()


def test_service_shutdown_joins_worker(qapp, tmp_path):
    database = tmp_path / "library.db"
    service = LibraryService(LibraryRepository(database), lambda: migrate(database),
                             scan, lambda p: Track(p))
    service.start("import", [])
    service.shutdown()
    assert service.pool.activeThreadCount() == 0
