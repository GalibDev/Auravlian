# Auravlian 0.8.0 — remaining desktop features and Windows build

Date: 2026-10-14. The request to finish the remaining work authorized continuation through Phases 5–8 without another phase approval pause. Implementation and local release preparation are delivered; clean-machine and broader compatibility validation remain explicitly unverified.

## Implemented

- Offline LRC parser: repeated timestamps, fractional seconds, global signed offsets, malformed-line tolerance and efficient position lookup. Matching `.lrc` files load in a background worker, with a 1 MB size cap and stale-result protection. Now Playing highlights the current line.
- Expanded Now Playing: side-by-side artwork/title, artwork-derived border accent, actual playback state/time, lyrics, spectrum and actions for fullscreen, mini-player and queue. Missing artwork remains an honest empty state. F11/Escape enter/leave fullscreen.
- Shared playback queue panel: view the authoritative order, select/play a track, remove a track or clear the queue. Compact always-on-top mini-player uses the same view model/service/engine and closes independently.
- System tray Show/Mini/Play-Pause/Next/Quit, optional close-to-tray preference, CLI file opening and keyboard shortcuts. Default close behavior still stops audio. Queued collection writes finish before exit.
- Audio-output selection with persisted device ID and fallback to the default when a selected device disappears.
- Real QAudioBufferOutput capture through Qt/FFmpeg. Bounded 32-band FFT uses at most 4,096 mono samples and runs at most every 50 ms. It supports UInt8/Int16/Int32/Float decoded formats. Silence produces zero bars; unsupported/unavailable capture displays a message. No random animation, fake progress or misleading EQ controls.
- Local M3U/M3U8 import/export with relative-path resolution, duplicate-name handling, atomic export, size limits and remote-stream rejection. Import validates metadata before creating playlist membership and refreshes the library.
- Reliability/performance: serialized concurrent schema migration startup, decoded-ready gating for history, bounded DSP work, stale lyrics protection, model/view large-table checks, accessible control names and keyboard operation.
- Windows release artifacts: original-symbol-derived icon, one-folder portable executable, portable ZIP, per-user Inno Setup installer, optional desktop shortcut, Start Menu shortcut, uninstaller, source build instructions and dependency notices.

The existing architecture, original logo source, settings, library persistence, playlists/favorites/history and single application-owned QMediaPlayer/QAudioOutput are retained. Optional multiband EQ was not implemented because this audio adapter has no tested processing backend; no EQ UI implies otherwise.

## Actual validation

Final source checks:

- **97 pytest tests passed in 18.74 seconds**, no skips/warnings.
- Ruff passed across `src`, `scripts` and `tests`.
- mypy passed across 73 source files.
- Editable version 0.8.0 installation succeeded; `pip check` reported no broken requirements.
- A full regression run was performed for Phase 7, extending the earlier Phase 4-only checks. The initial full run exposed an intermittent SQLite journal-mode startup lock race; serializing migration initialization resolved it, and subsequent full runs passed.

Synthetic benchmark on this host:

- 5,000 model rows; mean search/filter time **13.746 ms** over five queries.
- 4,096-sample FFT; mean processing time **0.558 ms** over 100 frames.
- Capture processing throttle **50 ms** (20 Hz maximum).

These numbers describe synthetic model/DSP work, not real-disk import throughput for thousands of files.

Source and packaged runtime diagnostics each generated a local PCM WAV and matching LRC, imported it, started actual decoded playback, paused and sought to 1,500 ms. JSON reported a 5,000 ms duration, actual history starts, **decoded_buffer_capture=true**, and **lyrics_lines=2**. The portable EXE diagnostic passed without using the Python source entry point.

The installer was compiled with Inno Setup 6.7.3 and installed into an isolated workspace directory on the current Windows 11 host. Installer exit **0**; installed EXE runtime diagnostic **passed**; Start Menu shortcut verified; uninstaller exit **0**; application EXE and test shortcut removed. The separate diagnostic database remained intact. This is a same-host installation/uninstallation test, not a fresh VM test.

Actual Qt screenshots were inspected for Now Playing with decoded audio bars and highlighted lyrics, the compact mini-player, queue and collection pages. The test audio was muted; human audible quality is not claimed.

## Local deliverables

- `dist/Auravlian/Auravlian.exe` — portable application, with adjacent `_internal` runtime folder.
- `dist/Auravlian-Portable-0.8.0-win64.zip` — 72,438,222 bytes.
- `dist/Auravlian-Setup-0.8.0.exe` — 62,852,366 bytes.
- `dist/SHA256SUMS.txt` — integrity checksums.

SHA-256:

```text
9e42b7ea7db06ba731b322ba97fb62fe8f01da0b08eb5250ad551c175a77fd05  Auravlian-Setup-0.8.0.exe
87b92f831d0d9e30154af453c23806b30ab0dbc3c3fc4d3deed2ee85403ac5e5  Auravlian-Portable-0.8.0-win64.zip
```

PyInstaller 6.11.1 bundled Python 3.12.14, Qt 6.8.3 Multimedia, the multimedia plugin and FFmpeg DLLs, NumPy, Mutagen, QSS and original logo resources. The icon was cropped/scaled/padded from the supplied symbol; it was not redrawn or recolored. Build outputs remain ignored by Git; source and build configuration can be pushed independently.

## Commands executed

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller==6.11.1
winget download --id JRSoftware.InnoSetup --exact --source winget --download-directory C:\projects\Auravlian\artifacts\tools --accept-source-agreements --accept-package-agreements --disable-interactivity
# Downloaded compiler installer was run silently, per-user, into .tools\InnoSetup.
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe main.py --smoke-test artifacts\runtime-smoke
.\.venv\Scripts\python.exe scripts/benchmark.py
.\.venv\Scripts\python.exe scripts/capture_desktop.py
.\.venv\Scripts\python.exe scripts/build_icon.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm packaging/windows.spec
& .\.tools\InnoSetup\ISCC.exe /Q packaging\installer.iss
# Portable/installed GUI EXEs were launched with Start-Process -WindowStyle Hidden -PassThru.
.\dist\Auravlian\Auravlian.exe --smoke-test C:\projects\Auravlian\artifacts\release-portable-smoke
& .\scripts\Test-Installer.ps1
Compress-Archive -Path dist/Auravlian -DestinationPath dist/Auravlian-Portable-0.8.0-win64.zip -Force
Get-FileHash dist/Auravlian-Setup-0.8.0.exe,dist/Auravlian-Portable-0.8.0-win64.zip -Algorithm SHA256
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m pip check
```

## Changed areas

Playback queue/service, bootstrap/CLI/diagnostics, library/playlist IO integration, SQLite startup, audio adapter/capture, Now Playing/Settings/MainWindow/sidebar, mini-player/queue/spectrum widgets, lyrics service/parser, packaging spec/installer/icon, build/benchmark/capture/installer-test scripts, new tests, README/changelog/build documentation, third-party notices and license texts. Existing migration-version assertion was updated in the preceding Phase 4 change. No original branding source was replaced.

## Remaining practical validation

- No clean VM/Windows Sandbox was available. Windows 10, clean systems without developer runtimes, other device drivers, hardware disconnect/reconnect and a broad codec/DPI matrix remain unverified. `BUILDING.md` gives the exact release validation checklist.
- Windows builds are unsigned. No signing certificate or public GitHub binary release is claimed. Local outputs are ready to install/test; source build configuration is versioned.
- Audio spectrum depends on a buffer-capable Qt/FFmpeg backend. LRC is local timed text, not online lyric retrieval. Direct-open track titles/artwork use available session/library metadata; no online metadata is fetched.
- No multiband EQ, global hardware-media-key integration or automatic moved-file reconciliation is claimed. M3U uses local filesystem paths only. Listening statistics count starts rather than listened duration.
- Disk I/O and metadata parsing cancellation remain cooperative between files. Artifact/source tests do not prove exhaustive leak-free or all-hardware behavior.

API/build references: [Qt decoded audio buffer output](https://doc.qt.io/qtforpython-6.8/PySide6/QtMultimedia/QAudioBufferOutput.html), [Inno Setup command-line behavior](https://jrsoftware.org/ishelp/topic_setupcmdline.htm). Build/runtime notices are included separately.
