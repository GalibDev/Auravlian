# Auravlian

**Feel Beyond Sound.** A native, offline-first Windows music player built with Python 3.12 and PySide6 Qt Widgets.

## Current status: Phase 4

Phase 4 adds persistent playlists, favorites, recently played history and dedicated Albums/Artists browsing. **Playlists → New** creates a playlist; select Library rows and choose **Add to playlist**. Rename/Delete manage the selected playlist, Remove removes selected membership, and Move up/down reorders one selected track. Deleting a playlist keeps your audio files and library entries. Duplicate names (ASCII case-insensitive) and empty names are rejected; names allow up to 120 characters. Playlist membership is unique per track.

Use **Library → Favorite selected** and **Favorites → Remove favorites**. Favorites and playlist membership survive rescans and missing-file marking. Albums group by album name and artist; Artists group by artist. Select a group and use Play selected/Play all. All pages reuse the same application player; collection edits do not replace the session queue.

**Recently Played** shows the latest 200 distinct paths, newest playback start first. A history event is recorded only when the real engine is Playing and decoded audio is ready, once per playback start. Pause/resume does not add another event; replaying after Stop or a repeat-one cycle does. Direct-open files also enter history without being automatically imported into the library. The displayed total counts playback starts, not completed listens or listening time. Home reflects actual favorites, playlist counts and recent titles.

Collection database reads/writes run serially through a separate background pool, with transactional membership edits. Close waits for queued collection writes before destruction. The schema upgrades existing libraries to version 2, retaining tracks and their IDs.

The native foundation includes nine navigation destinations, the Aurora dark design system, original-symbol branding, saved window geometry and startup preferences, and rotating JSON logs. Actual local playback uses exactly one application-owned QMediaPlayer and QAudioOutput, a pure-Python queue, a PlaybackService and a shared PlayerViewModel. Phase 3 adds a persistent SQLite library with background import, metadata, artwork thumbnails, search, sorting and rescans.

Use **Home → Open audio files**, **Now Playing → Open audio files**, or **File → Open audio files (Ctrl+O)** for immediate session playback. Selecting files replaces the session queue and begins playback; cancelling preserves playback. Direct-open titles use filenames. Opening files is separate from persistent library import.

Use **Library → Import files / Import folder** to add music permanently to the local database. Folders scan recursively without following nested directory symlinks. Supported scanner extensions are MP3, FLAC, WAV, Ogg, M4A, AAC, WMA, Opus and AIFF; actual metadata/playback support depends on file content and codecs. Canonical path identity deduplicates repeated/overlapping imports, not distinct copies with identical audio content. Untagged valid files use filename, Unknown artist and Unknown album. Corrupt or unreadable inputs are skipped with warnings.

Search matches all entered words across title, artist and album, ignoring case. Click column headers to sort (duration sorts numerically). Double-click an available row or select rows and choose **Play selected**; the current player/queue is reused and metadata titles are retained. Missing rows remain searchable but are excluded from playback. Home shows actual imported album/artist groups, favorites, playlists and recent titles.

**Rescan** revisits remembered folders and individually imported paths, refreshes metadata, discovers additions and marks absent tracks Missing. It preserves track IDs and creation timestamps; rows are never deleted by rescans. Restored files become available again. **Cancel** keeps already processed imports and skips the missing-status sweep. Only one library job runs at a time. Close requests cancel active work and defer window destruction while the worker finishes; application shutdown joins the pool. Cancellation is cooperative between files, so a slow filesystem or decoder call can delay completion.

Embedded APIC/FLAC/MP4/Vorbis artwork is extracted where available into content-addressed PNG thumbnails (at most 192×192). Invalid/oversized images fall back to no artwork; extraction/cache errors are logged while valid audio metadata remains importable. GUI icons use a bounded 128-entry cache. No generated artwork substitutes for missing covers.

The persistent bar supports play/pause, stop, next, previous, seek, volume, mute, shuffle and repeat off/one/all. Empty-queue controls are disabled; Play and seek remain disabled while loading. Volume and mute are saved in QSettings. Closing the main window stops playback; navigating between pages preserves it.

Queue rules: fixed seed `0` produces reproducible shuffle order, anchors the current track, and visits each other track once per cycle. Turning shuffle off restores file-selection order without changing the active track. Repeat-one applies to natural completion; manual Next advances. Repeat-all wraps in both directions. With repeat off, completion at the last track stops. Previous restarts the current track after three seconds, otherwise moves back. Native queued transport slots keep Qt objects on the application thread and avoid a reproduced immediate-stop backend hang.

Missing paths are reported, duplicate selections are removed, decode failures skip forward to the next unfailed track, and exhausting the queue stops retrying even under repeat-all. Device errors keep the selected track for retry. Loading/stalls have a 15-second timeout. Errors appear in the playback bar and Now Playing, with complete messages in tooltips and logs. Format support depends on Qt's installed multimedia backend; no format is advertised as guaranteed.

The Figma Home reference guides the sidebar, hero, cards, spacing and palette. Its demo music is intentionally replaced with empty states. The original logo PNG is preserved byte-for-byte; the sidebar displays a crop above the old wordmark alongside the new Auravlian name. No replacement symbol is generated. The Figma temporary A monogram is superseded by the supplied original symbol.

## Launch on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe main.py
```

After installation, the `auravlian` console entry point also launches the app. No browser or network connection is required at runtime.

## Architecture

`src/auravlian/app` owns startup, dependencies and lifecycle. `presentation` owns Qt pages, QAbstractTableModel/QSortFilterProxyModel, library/player view models and theme tokens. `domain` owns immutable track snapshots, the authoritative PlaybackQueue, RepeatMode and port protocols. `application` orchestrates playback, background library jobs and matching. Infrastructure provides the Qt audio adapter, SQLite connections/migrations/repository, scanner, Mutagen metadata reader and artwork cache. Every database operation creates and closes its connection on the calling worker thread; no connection is shared across threads. Imports write transactional batches of 64, with foreign keys and WAL enabled.

Files for later phases remain explicitly reserved modules. Albums, Artists, Playlists, Favorites and Recently Played now share reusable collection pages with model/view track tables. Home, Library, collections and Now Playing use the same session player. The source-root `assets` directory preserves provided branding, while packaged assets live inside the Python package so installed launches do not depend on the working directory.

User settings use QSettings under `HKEY_CURRENT_USER\Software\Auravlian\Auravlian`. Logs, `library.sqlite3` and the `artwork` cache use Qt's per-user AppLocalDataLocation, never the installation directory. Tests/previews use isolated INI sessions and keep their databases/caches beside their INI. Geometry and last-page state save on close; startup preference saves immediately. Schema version 2 adds playlists, ordered playlist membership, favorites and listening history to the normalized library; migrations are transactional and reject newer unknown schemas.

## Validation

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/capture_preview.py
.\.venv\Scripts\python.exe scripts/playback_smoke.py
.\.venv\Scripts\python.exe scripts/library_smoke.py
.\.venv\Scripts\python.exe scripts/phase4_smoke.py
# Optional quiet physical-output diagnostic tone:
.\.venv\Scripts\python.exe scripts/playback_smoke.py --audible
```

Phase 4 validation intentionally runs only the new focused tests, per the user's requested scope:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_phase4_collections.py tests/ui/test_phase4_pages.py
```

These cover upgrade preservation, playlist CRUD/order/dedup/validation, favorites, retained missing-file membership, recent history, asynchronous error recovery, real playback-start recording and collection UI actions. See `PHASE4_REPORT.md` for actual results. Earlier phase test results remain documented in their own reports; their suites were not rerun in Phase 4. The prior migration test's schema-version assertion is updated from 1 to 2 to reflect this migration.

Manual checks: launch at 100%, 125%, 150% and 200% Windows scaling; resize to 960×700; traverse navigation with mouse and keyboard; change the startup preference; close and reopen. Preview screenshots are generated from actual Qt widgets in ignored `artifacts/`.

For physical playback: open two known-good local files, listen through the selected Windows default output, pause/resume, drag and keyboard-adjust seek, change volume/mute, switch tracks rapidly, test all repeat modes, navigate pages, disconnect/reconnect output, try a corrupt file and retry, then close while playing. Confirm sound stops on close. Test MP3/FLAC/AAC/Ogg separately; the generated WAV checks do not certify every codec or device. The smoke script checks actual UI/backend state and writes JSON/screenshots, but cannot certify sound quality by listening.

## Phase plan

1. Foundation, branding, design system, shells and startup tests — implemented.
2. One QMediaPlayer/QAudioOutput, authoritative queue, real playback and error handling — implemented.
3. SQLite migrations/repositories, background import, metadata, artwork, model/view library and search — implemented.
4. Playlists, favorites, history, albums and artists — implemented.
5. Expanded Now Playing, lyrics, queue, mini-player, shortcuts and desktop integrations.
6. Real audio-buffer visualization and device selection; optional DSP feasibility.
7. Regression, performance, accessibility and Windows compatibility.
8. Portable executable, original-symbol icon, Inno Setup installer and clean-machine validation.

Phase 4 preserves the existing window, pinned dependencies, logo, settings, player and queue. Phase 5 requires approval for the expanded Now Playing experience, lyrics, queue page, mini-player and desktop integrations.

## Packaging

Packaging is planned for Phase 8. `packaging/windows.spec` and `packaging/installer.iss` document their deferred status. No executable or installer is claimed or shipped in Phase 1. Later release validation must inspect Qt Multimedia runtime inclusion, physical output devices, actual audio formats, large libraries, and a clean Windows installation/uninstallation.

Design reference: [Auravlian UI kit](https://www.figma.com/design/8ks43deppuJYizCWGV0ZTS/Untitled?node-id=1-2).

