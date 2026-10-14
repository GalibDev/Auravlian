# Phase 4 delivery — 2026-10-14

## Scope

Focused only on Phase 4 as requested. Read existing integration points needed to connect collection storage, playback events and pages; did not perform a separate review or test run of earlier phases.

Implemented persistent playlist CRUD, unique membership, track removal/reordering, favorites, real listening history and Albums/Artists browsing. The existing player/output pair, queue, logo, styling and QSettings integration are reused. Phase 5+ features were not added.

## Behavior

- Schema version 2 transactionally adds playlists, playlist_tracks, favorites and listening_history. Upgrading a v1 database retains existing tracks. Foreign keys protect track references; deleting a playlist cascades only its membership, never music files or library tracks.
- Playlist names trim whitespace and require 1–120 characters; ASCII case-insensitive duplicate names are rejected. Adding the same track twice does not duplicate membership. Add/reorder are transactional; invalid membership lists roll back. Reordering uses temporary negative positions to avoid UNIQUE collisions.
- Library selections can be favorited or added to a chosen playlist. Playlists support New, Rename, Delete, Remove, Move up/down, Play selected and Play all. Favorites has an explicit Remove favorites action. Missing imported tracks retain membership and are excluded from playback.
- Album/artist selectors use actual library metadata. Album groups distinguish artists; track tables reuse the model/view infrastructure and existing artwork. Collection playback uses the same PlaybackService as every other page; editing collections preserves the current queue.
- PlaybackService emits track_started only when Playing and decoded audio ready, once per start generation. Pause/resume does not count twice. Repeat/replay starts can count again. History stores direct-open file snapshots without silently importing them, and shows the newest 200 unique paths plus the persisted total start count.
- SQLite work and snapshots run in a serialized QThreadPool worker. UI signals refresh pages and Home summaries. Close waits for pending writes; application shutdown joins the pool. Worker errors appear in page status text.

## Files changed

Modified:

- `src/auravlian/app/container.py`
- `src/auravlian/application/playback_service.py`
- `src/auravlian/application/playlist_service.py`
- `src/auravlian/domain/interfaces/repositories.py`
- `src/auravlian/domain/models/playlist.py`
- `src/auravlian/infrastructure/database/migrations.py`
- `src/auravlian/presentation/main_window.py`
- `src/auravlian/presentation/pages/home.py`
- `src/auravlian/presentation/pages/library.py`
- `src/auravlian/presentation/theme/styles.qss`
- `src/auravlian/presentation/viewmodels/playlist_vm.py`
- `tests/integration/test_library.py` — only the expected schema version changes from 1 to 2; this old suite was not run.
- `README.md`, `CHANGELOG.md`

Added:

- `src/auravlian/infrastructure/database/repositories/collection_repository.py`
- `src/auravlian/presentation/pages/collections.py`
- `tests/integration/test_phase4_collections.py`
- `tests/ui/test_phase4_pages.py`
- `scripts/phase4_smoke.py`
- `PHASE4_REPORT.md`

## Executed checks

```powershell
.\.venv\Scripts\python.exe -m ruff check src scripts/phase4_smoke.py tests/integration/test_phase4_collections.py tests/ui/test_phase4_pages.py
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_phase4_collections.py tests/ui/test_phase4_pages.py --tb=short
.\.venv\Scripts\python.exe scripts/phase4_smoke.py
```

**13 Phase 4 tests passed**; Ruff passed and mypy passed across 66 source files. No older-phase suite was run, and no claim is made about a full regression run in this phase.

Tests cover v1→v2 data preservation, playlist CRUD, duplicate/empty-name validation, atomic adds, ordering, favorites and rescan-retained references, recent unique history, persisted counts, asynchronous queue/error recovery, start-event gating, real Qt WAV playback recording, album/artist groups, Library actions, rename/delete UI, error visibility and queue preservation during edits.

The isolated real-WAV smoke passed. It created one Evening Sessions playlist with three tracks ordered Blue Horizon → Midnight → Aurora, one favorite and an actual Aurora playback-start history entry. Repeated smoke execution retained the same playlist/favorite membership and increased the stored start count. Generated files/database are under ignored `artifacts/phase4-smoke`, not the user's library. Output was muted; human listening was not verified.

Actual Qt screenshots for all five new pages and the 960×700 playlist layout were inspected. The large layout uses the existing 1440×900 logical window at host scaling. Collection controls use two rows so the smaller window stays usable; long labels elide with full group names in tooltips.

## How to use

Launch `.\.venv\Scripts\python.exe main.py`. Create a playlist on Playlists, select songs in Library and choose Add to playlist. Use Favorite selected to save favorites. Albums/Artists open grouped songs; Play selected/Play all reuses the current player. Recently Played fills from actual playback starts. Move up/down reorders one selected playlist track. Delete asks confirmation and keeps local audio files.

## Limits

History counts starts, not completed listens or listened duration. Recent UI displays up to 200 distinct paths; underlying events remain stored. Album grouping uses the artist metadata available in the current library, without album-artist/disc-number reconciliation. Reorder uses buttons, not drag/drop. M3U import/export, lyrics, expanded Now Playing, mini-player and desktop integrations remain later work. Earlier-phase regression suites were deliberately not rerun per the request.

Phase 4 stops here pending approval for Phase 5.
