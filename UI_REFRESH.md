# Nuclear-inspired desktop layout

Implemented an artwork-first Home music strip (up to 12 local tracks), slimmer
sidebar, global library search, resizable embedded queue with persisted visibility,
compact playback controls with artwork, and album/artist/playlist detail headers.
Original branding and the existing shared playback engine remain in use. Nuclear
screenshots informed layout choices; no Nuclear source or assets were copied.

Home music cards play their selected local track. Collection cards navigate to
their respective pages. Missing files are disabled and absent artwork uses a music
glyph. The welcome banner appears for an empty library. Use Library for the full
collection. Queue actions require a selection where relevant.

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/capture_desktop.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm packaging/windows.spec
& '.tools\InnoSetup\ISCC.exe' packaging\installer.iss
```

Ruff passed; mypy passed for 74 source files; the full suite passed 103 tests.
After the final card-height adjustment, all 6 Home/layout tests passed again.
Source playback was verified with generated muted PCM audio; artwork layout was
visually checked at 1440×900 and 960×700 logical pixels. Test covers and songs in
preview screenshots are isolated fixtures, not additions to the user's library.
Human listening and a clean Windows VM were not performed.
The rebuilt portable EXE also passed its isolated `--smoke-test`: 5000 ms
duration, pause and seek to 1500 ms, one imported track and history start,
decoded audio capture, and two local lyric lines.

The original release report documents the earlier build. Updated local artifacts
keep the existing 0.8.0 filenames; current checksums are in `dist/SHA256SUMS.txt`.
