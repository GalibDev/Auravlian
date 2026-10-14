# Changelog

## Phase 4 — Personal collections

- Schema version 2 upgrades libraries with playlists, ordered membership, favorites and listening history.
- Create/rename/delete playlists, add/remove songs and reorder with Move up/down.
- Favorite Library selections and remove favorites from their dedicated page.
- Album/artist drill-down and playable collections share the existing player/queue.
- Actual decoded playback starts populate persisted recent history without pause/resume duplicates.
- Background serialized collection writes, actionable errors and Home collection summaries.
- Phase 4 focused tests and an isolated real-WAV visual/persistence smoke; older suites intentionally not rerun.

## Phase 3 — Persistent local library

- Versioned transactional SQLite schema and normalized tracks, artists, albums and folders.
- Background QRunnable/QThreadPool file/folder import, recursive scanning and path deduplication.
- Mutagen metadata/fallbacks and content-addressed embedded-artwork thumbnails.
- Searchable/sortable Qt model/view Library, metadata-preserving playback and Home collection counts.
- Rescans preserve track identities, detect missing files and restore availability; cancellation saves partial work.
- Worker-owned database connections, bounded warning details, cooperative shutdown and regression coverage.
- Original Phase 1/2 tests, branding, settings and shared engine preserved; Phase 4 features remain deferred.

## Phase 2 — Local playback

- One application-owned Qt Multimedia player/output adapter, pure playback queue, service and shared view model.
- Actual file opening, transport, seeking, volume/mute, deterministic shuffle and repeat off/one/all.
- Signal-driven persistent controls and shared Now Playing state; audio preferences persist through QSettings.
- Missing/corrupt media handling, bounded recovery, loading timeout and output-device errors.
- Native queued transport slots resolve an immediate-stop hang while retaining the original Qt 6.8.3 pin.
- Real generated-WAV integration coverage and an isolated optional audible UI smoke script.
- Phase 1 tests, branding, navigation and settings retained; no Phase 3 features added.

## 0.1.0 — Phase 1

- Native PySide6 foundation and requested layered project layout.
- Figma-informed dark Home layout, nine page shells and persistent playback shell.
- Unmodified original logo asset with symbol-only presentation crop.
- QSettings persistence, safe packaged assets and per-user rotating logging.
- Startup/navigation and preference regression coverage.

