# Auravlian

**Feel Beyond Sound.** A native, offline-first Windows music player built with Python 3.12 and PySide6 Qt Widgets.

## Current status: Phase 1

The executable foundation includes nine navigable page shells, the Aurora dark design system, a persistent disabled playback bar, meaningful empty states, original-symbol branding, saved window geometry and startup preferences, and rotating JSON logs. No music is imported or played yet.

The Figma Home reference guides the sidebar, hero, cards, spacing and palette. Its demo music is intentionally replaced with empty states. The original logo PNG is preserved byte-for-byte; the sidebar displays a crop above the old wordmark alongside the new Auravlian name. No replacement symbol is generated. The Figma temporary A monogram is superseded by the supplied original symbol.

## Launch on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe main.py
```

After installation, the `auravlian` console entry point also launches the app. No browser or network connection is required at runtime.

## Architecture

`src/auravlian/app` owns startup, dependencies and lifecycle. `presentation` owns Qt pages, reusable widgets and theme tokens. `domain` defines the future pure models and queue; `application` will orchestrate use cases; `infrastructure` will implement audio, SQLite, scanners, metadata and artwork adapters. `shared` contains paths, errors and application events.

Files for later phases are explicitly reserved modules, not implemented services. Phase 1 pages use a shared empty-state component; per-page modules are extension boundaries. The source-root `assets` directory preserves provided branding, while packaged assets live inside the Python package so installed launches do not depend on the working directory.

User settings use QSettings under `HKEY_CURRENT_USER\Software\Auravlian\Auravlian`. Logs use Qt's per-user AppLocalDataLocation, never the installation directory. Geometry and last-page state save on close; startup preference saves immediately.

## Validation

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/capture_preview.py
```

UI tests use isolated INI settings and cover startup, all navigation destinations, persistent playback shell, disabled future controls, settings persistence, geometry/page restoration, invalid-page fallback, original asset integrity and minimum window size.

Manual checks: launch at 100%, 125%, 150% and 200% Windows scaling; resize to 960×700; traverse navigation with mouse and keyboard; change the startup preference; close and reopen. Preview screenshots are generated from actual Qt widgets in ignored `artifacts/`.

## Phase plan

1. Foundation, branding, design system, shells and startup tests — implemented.
2. One QMediaPlayer/QAudioOutput, authoritative queue, real playback and error handling.
3. SQLite migrations/repositories, background import, metadata, artwork, model/view library and search.
4. Playlists, favorites, history, albums and artists.
5. Expanded Now Playing, lyrics, queue, mini-player, shortcuts and desktop integrations.
6. Real audio-buffer visualization and device selection; optional DSP feasibility.
7. Regression, performance, accessibility and Windows compatibility.
8. Portable executable, original-symbol icon, Inno Setup installer and clean-machine validation.

Phase 2 must reuse the current window, dependencies and persistent bar. Queue logic stays separate from Qt audio and gets repeat/shuffle regression tests. Playback controls become enabled only when wired to real audio signals.

## Packaging

Packaging is planned for Phase 8. `packaging/windows.spec` and `packaging/installer.iss` document their deferred status. No executable or installer is claimed or shipped in Phase 1. Later release validation must inspect Qt Multimedia runtime inclusion, physical output devices, actual audio formats, large libraries, and a clean Windows installation/uninstallation.

Design reference: [Auravlian UI kit](https://www.figma.com/design/8ks43deppuJYizCWGV0ZTS/Untitled?node-id=1-2).

