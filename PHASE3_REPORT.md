# Phase 3 delivery — 2026-10-14

## Delivered

Inspected the existing source and tests before editing. Baseline: **58 tests passed**. All prior test files remain unchanged, including the original 17 Phase 1 tests. Logo assets, playback adapter, queue behavior, audio dependency pins, QSettings preferences and Figma-inspired dark styling are preserved.

Implemented:

- SQLite schema version 1 with normalized artists, albums, tracks and folder roots; indexed fields, WAL, foreign keys, explicit transactional migrations and rejection of unknown future schemas.
- Repository operations with a fresh connection owned/closed by the calling thread; batched transactional upserts preserve track IDs and added timestamps.
- QThreadPool/QRunnable background jobs for initial load, individual-file import, recursive-folder import and rescan. Only one job runs at a time; signals deliver snapshots/progress to GUI-owned objects.
- Canonical path deduplication across repeated and overlapping imports, case-insensitive supported extensions and nested-directory-symlink avoidance.
- Mutagen title/artist/album/duration extraction with valid untagged-file fallbacks. Corrupt inputs report warnings. Embedded APIC/FLAC/MP4/Vorbis covers generate atomic content-addressed thumbnails; artwork failures do not discard otherwise valid tracks.
- Searchable/sortable QAbstractTableModel Library with no widgets per song, numeric duration sorting, bounded GUI artwork icon cache, missing-track state, file/folder dialogs, rescan and cancel controls.
- Double-click/Play selected routes imported snapshots with their metadata to the existing shared PlaybackService and engine. No new QMediaPlayer or QAudioOutput is created by library pages/jobs.
- Missing-file detection on rescan, restoration when files return, and retained rows/identities for future playlist references. Cancelled scans do not sweep missing flags and keep processed imports.
- Close requests cancel active jobs and defer closing until completion; application shutdown joins the worker pool. Home has a Library navigation action and reflects actual imported album/artist group counts.

No playlist CRUD, favorites, history, dedicated Albums/Artists browsing, lyrics, visualizer, installer or later-phase feature was implemented.

## Changed files

Modified:

- `src/auravlian/app/container.py`
- `src/auravlian/application/library_service.py`
- `src/auravlian/application/playback_service.py`
- `src/auravlian/application/search_service.py`
- `src/auravlian/domain/interfaces/repositories.py`
- `src/auravlian/domain/models/track.py`
- `src/auravlian/infrastructure/cache/artwork_cache.py`
- `src/auravlian/infrastructure/database/connection.py`
- `src/auravlian/infrastructure/database/migrations.py`
- `src/auravlian/infrastructure/filesystem/scanner.py`
- `src/auravlian/infrastructure/metadata/mutagen_reader.py`
- `src/auravlian/presentation/main_window.py`
- `src/auravlian/presentation/pages/home.py`
- `src/auravlian/presentation/pages/library.py`
- `src/auravlian/presentation/theme/styles.qss`
- `src/auravlian/presentation/viewmodels/library_vm.py`
- `src/auravlian/presentation/widgets/track_table.py`
- `README.md`, `CHANGELOG.md`

Added:

- `src/auravlian/infrastructure/database/repositories/library_repository.py`
- `tests/integration/test_library.py`
- `tests/integration/test_library_reliability.py`
- `tests/ui/test_library_ui.py`
- `scripts/library_smoke.py`
- `PHASE3_REPORT.md`

## Executed validation

PowerShell commands from `C:\projects\Auravlian`:

```powershell
git status --short
git diff --stat
git diff -- tests/ui/test_foundation.py tests/conftest.py tests/integration/test_qt_playback.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe scripts/library_smoke.py
.\.venv\Scripts\python.exe scripts/playback_smoke.py
.\.venv\Scripts\python.exe scripts/capture_preview.py
```

Validation: **75 tests passed**, no skips/warnings; Ruff passed; mypy passed across 64 source files. The new 17 cases cover migrations, concurrent initialization/writes, rollback, identity/reference preservation, tagged/untagged metadata, extracted artwork, recursive/deduplicated scanning, persisted imports/rescans/restoration, cancellation, shutdown, deferred window close during active work, worker responsiveness/thread ownership, warning/error handling, 5,000-row model search/sort and UI file-dialog/playback routing. All 58 earlier tests remain unchanged and pass.

The generated-media smoke imported three tagged WAVs into an isolated database, found one result for `aurora artist`, and reached real Qt Playing state with the metadata title **Aurora** through the existing engine. Repeated runs reported zero duplicate additions. The existing playback smoke also passed: actual duration 8,000 ms, advancing position, pause/seek at 2,500 ms, Stop at 0 ms. Smoke output was muted; human listening was not verified.

Library and small Home screenshots were rendered from actual Qt widgets and visually inspected. Test/smoke databases, media and screenshots are isolated under pytest temporary directories or ignored `artifacts/`, not the user's actual library.

An initial smoke helper timed out while repeatedly using QTest.qWait around Python worker work. Switching the helper to a real QEventLoop/QTimer wait allowed background Python work to progress and the smoke passed. Production already runs QApplication.exec. The implementation also documents a narrow mypy ignore for PySide 6.8 QImage.save's inaccurate format stub, verified against the runtime and artwork tests.

## Usage, data and limits

Launch: `.\.venv\Scripts\python.exe main.py`. Open Library, choose Import files or Import folder, then search/sort and double-click or Play selected. Rescan discovers folder additions and flags missing tracked files. Close/reopen preserves the library and settings.

Normal user database/cache live under Qt AppLocalDataLocation (`library.sqlite3`, `artwork/`). Isolated INI sessions store them in a `library/` directory beside the INI. Installation directories are never used for normal writable data.

Duplicate detection uses canonical paths, not audio-content hashing. Renamed/moved files appear as a missing old path plus a new imported path; automatic move reconciliation is deferred. Missing rows are retained, and import does not delete user files. Folder watching is manual Rescan, not a filesystem watcher.

The 5,000-row test validates model/filter/sort behavior, not end-to-end throughput of a 5,000-file real library. Real metadata/artwork fixtures use WAV/ID3; all container/tag variants and physical devices still require manual testing. Artwork without a supported embedded cover stays blank, with no generated replacement; old content-addressed cache files are not garbage-collected in this phase. Cancellation is cooperative between files; a slow operating-system I/O or metadata call can delay shutdown. Dedicated album/artist pages and playlist/history/favorite tables remain Phase 4 work.

Phase 3 stops here pending approval for Phase 4.
