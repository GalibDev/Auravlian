# Auravlian

**Feel Beyond Sound.** A native, offline-first Windows music player built with Python 3.12 and PySide6 Qt Widgets.

## Current status: Phase 2

The native foundation includes nine navigation destinations, the Aurora dark design system, original-symbol branding, saved window geometry and startup preferences, and rotating JSON logs. Phase 2 adds actual local playback through exactly one application-owned QMediaPlayer and QAudioOutput, a pure-Python queue, a PlaybackService and a shared PlayerViewModel. Library import and persistence remain Phase 3 work.

Use **Home → Open audio files**, **Now Playing → Open audio files**, or **File → Open audio files (Ctrl+O)**. Selecting files replaces the session queue and begins playback. Cancelling preserves playback. Tracks use their filename as a title until metadata support arrives. Opening files is not a library import.

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

`src/auravlian/app` owns startup, dependencies and lifecycle. `presentation` owns Qt pages, reusable widgets, the shared player view model and theme tokens. `domain` owns the pure track model, authoritative PlaybackQueue, RepeatMode and AudioPort protocol; `application` orchestrates playback; `infrastructure/audio` owns the single Qt player/output adapter. SQLite, scanners, metadata and artwork remain reserved. `shared` contains paths, errors and application events.

Files for later phases are explicitly reserved modules, not implemented services. Library-related pages retain shared empty states. Home and Now Playing connect to the same session player. The source-root `assets` directory preserves provided branding, while packaged assets live inside the Python package so installed launches do not depend on the working directory.

User settings use QSettings under `HKEY_CURRENT_USER\Software\Auravlian\Auravlian`. Logs use Qt's per-user AppLocalDataLocation, never the installation directory. Geometry and last-page state save on close; startup preference saves immediately.

## Validation

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/capture_preview.py
.\.venv\Scripts\python.exe scripts/playback_smoke.py
# Optional quiet physical-output diagnostic tone:
.\.venv\Scripts\python.exe scripts/playback_smoke.py --audible
```

All 17 Phase 1 tests remain unchanged. Additional tests cover queue ordering, deterministic shuffle, repeat, completion, bounded error recovery, stale callbacks, transport commands, UI signals, shared engine ownership, device errors, loading timeout and volume/mute persistence. Integration tests generate isolated PCM WAVs and exercise real Qt decoding, timing, pause/seek/resume/stop, repeat, transitions, corrupt-input recovery and rapid switching. Real-media tests skip explicitly when the host has no audio output device; no skips occurred on the development host. See `PHASE2_REPORT.md` for executed results.

Manual checks: launch at 100%, 125%, 150% and 200% Windows scaling; resize to 960×700; traverse navigation with mouse and keyboard; change the startup preference; close and reopen. Preview screenshots are generated from actual Qt widgets in ignored `artifacts/`.

For physical playback: open two known-good local files, listen through the selected Windows default output, pause/resume, drag and keyboard-adjust seek, change volume/mute, switch tracks rapidly, test all repeat modes, navigate pages, disconnect/reconnect output, try a corrupt file and retry, then close while playing. Confirm sound stops on close. Test MP3/FLAC/AAC/Ogg separately; the generated WAV checks do not certify every codec or device. The smoke script checks actual UI/backend state and writes JSON/screenshots, but cannot certify sound quality by listening.

## Phase plan

1. Foundation, branding, design system, shells and startup tests — implemented.
2. One QMediaPlayer/QAudioOutput, authoritative queue, real playback and error handling — implemented.
3. SQLite migrations/repositories, background import, metadata, artwork, model/view library and search.
4. Playlists, favorites, history, albums and artists.
5. Expanded Now Playing, lyrics, queue, mini-player, shortcuts and desktop integrations.
6. Real audio-buffer visualization and device selection; optional DSP feasibility.
7. Regression, performance, accessibility and Windows compatibility.
8. Portable executable, original-symbol icon, Inno Setup installer and clean-machine validation.

Phase 2 reuses the existing window, pinned dependencies and persistent bar. Phase 3 requires approval and will add SQLite/library scanning without replacing the shared player or queue.

## Packaging

Packaging is planned for Phase 8. `packaging/windows.spec` and `packaging/installer.iss` document their deferred status. No executable or installer is claimed or shipped in Phase 1. Later release validation must inspect Qt Multimedia runtime inclusion, physical output devices, actual audio formats, large libraries, and a clean Windows installation/uninstallation.

Design reference: [Auravlian UI kit](https://www.figma.com/design/8ks43deppuJYizCWGV0ZTS/Untitled?node-id=1-2).

