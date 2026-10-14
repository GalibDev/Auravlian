# Phase 1 delivery — 2026-10-14

## Implemented

- Runnable native Qt Widgets app and installed `auravlian` entry point.
- Sidebar navigation across Home, Library, Albums, Artists, Playlists, Favorites, Recently Played, Now Playing and Settings.
- Persistent playback shell whose transport, seek and volume controls are disabled.
- Dark token-based styling, Figma Home composition and honest empty library states.
- Original logo preserved unchanged; display-only crop excludes the Auralis wordmark.
- QSettings startup preference, last page and geometry persistence.
- Rotating structured logs and safe per-user writable paths.
- Modular structure with explicitly reserved later-phase service boundaries.

## Files

All implementation files are new; no existing source code was present or modified. The supplied `.fig` and original logo remain unchanged.

- Root: `main.py`, `pyproject.toml`, `.gitignore`, `README.md`, `CHANGELOG.md`, this report.
- `app`: bootstrap, container and lifecycle.
- `presentation`: main window, theme tokens/QSS, Home and Settings, shared empty-page component, sidebar and playback bar. Other page modules are reserved extension boundaries; their working shells are composed by the main window.
- `shared`: events, errors and paths.
- `domain`, `application`, `infrastructure`, `presentation/viewmodels`: requested modules reserved for future phases; no fake services.
- Assets: byte-identical original logo in source assets and packaged resources. Icons/placeholders directories reserved.
- Tests: isolated Qt fixtures and foundation UI regression tests; unit/integration directories reserved.
- Scripts: actual Qt preview capture.
- Packaging: documented Phase 8 placeholders that intentionally reject premature builds.

## Executed commands and outcomes

Commands were run in PowerShell using the bundled Python 3.12.14 to create `.venv`:

```powershell
<bundled-python> -m venv .venv
.\.venv\Scripts\python.exe -m pip install PySide6==6.8.3 mutagen==1.47.0 numpy==2.2.6 pytest==8.3.5 pytest-qt==4.4.0 ruff==0.11.13 mypy==1.15.0
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m ruff check . --fix
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/capture_preview.py
git ls-remote https://github.com/GalibDev/Auravlian.git
git init -b main
git remote add origin https://github.com/GalibDev/Auravlian.git
```

Final validation: Ruff passed; mypy passed across 63 source files; **17 tests passed in 3.32 seconds**. Editable installation succeeded. Real Qt screenshots were generated and visually inspected at 1440×900 and 960×700 logical window sizes on the host's 125% scaling.

An initial mypy failure required explicit bool conversion for QSettings. The first test run had one checkbox test failure because the simulated click hit unused checkbox row space; the test now clicks the indicator. Synchronous signal assertions now use QSignalSpy, removing the pytest-qt timeout-disconnection warnings. Final run had no warnings.

## Figma and visual verification

Read Home node `1:2` from the supplied Figma file with design context and screenshot. Its colors, sidebar width, hero, four-card section and persistent bottom bar inform the implementation. The temporary Figma A monogram is replaced by the supplied original symbol, as required. Demo songs, artwork monograms and playback progress are replaced by empty states. The implementation is a Phase 1 adaptation, not a pixel-identical recreation of every populated design screen. Settings uses only the implemented startup preference; later controls are not represented as functional.

## Known limitations and next phase

Audio playback, imports, SQLite, queue, playlists, history, lyrics, device selection, visualizer, executable and installer are not implemented. No real-audio or clean-machine installer tests are claimed. Windows scaling beyond the host's 125% has manual instructions in README and has not been physically verified.

Launch: `.\.venv\Scripts\python.exe main.py`.

Ready for Phase 2: connect one application-owned QMediaPlayer/QAudioOutput adapter and authoritative domain queue to the existing persistent shell, with repeat/shuffle/error regression tests. Phase 2 requires user approval under the supplied phased workflow.

