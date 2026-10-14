# Changelog

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

