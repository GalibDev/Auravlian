# Phase 2 delivery — 2026-10-14

## Scope and implementation

Inspected the Phase 1 source and ran its baseline before editing: **17 passed in 3.37s**. All original test files and fixtures remain unchanged, as do the original logo, sidebar branding and Python/PySide dependency pins. Existing startup settings, geometry restoration, nine navigation destinations and dark visual system are retained.

- `Container.player` lazily creates and caches one application-owned `QtAudioEngine`, one pure `PlaybackQueue`, one `PlaybackService` and one `PlayerViewModel` on the application thread. The adapter creates exactly one QMediaPlayer and one QAudioOutput, parented to its lifetime. Home, Now Playing and the persistent bar use the same dependencies.
- Domain queue implements selection order, deterministic seeded shuffle, current-track preservation, next/previous, completion and repeat off/one/all without importing Qt.
- PlaybackService validates/deduplicates local paths, replaces the session queue, orchestrates real transport and bounds error recovery. Failures cannot loop indefinitely under repeat-all; repeat-one does not trap manual Next or error recovery. Pending completion/recovery callbacks are invalidated by Stop, new media and shutdown.
- The adapter connects actual multimedia state, position, duration, seekability, completion and error signals. Native queued commands execute on the owning thread, preserving stop/source/play order. Wrong-thread commands are rejected. A 15-second loading/stall watchdog reports timeout. Missing devices and files without playable audio produce actionable errors.
- Persistent controls implement play/pause, stop, next, previous, drag/keyboard seeking, volume, mute, shuffle and repeat. Empty controls stay disabled; Play/seek respect loading/readiness. Home and Now Playing expose Open Files, also available under File/Ctrl+O. File-dialog cancellation preserves playback. Errors remain visible in both views and logs.
- Volume/mute persist through QSettings; position events do not repeatedly rewrite unchanged audio preferences. Page navigation preserves playback. Main-window close stops playback, and application quit invalidates callbacks.

No SQLite, library scanning, metadata import, artwork processing, playlist CRUD, lyrics, spectrum visualizer, device-selection UI, installer or other later-phase feature was added.

## Files changed

Modified:

- `src/auravlian/app/container.py`
- `src/auravlian/application/playback_service.py`
- `src/auravlian/domain/interfaces/audio_port.py`
- `src/auravlian/domain/models/track.py`
- `src/auravlian/domain/playback/queue.py`
- `src/auravlian/domain/playback/repeat_mode.py`
- `src/auravlian/infrastructure/audio/qt_audio_engine.py`
- `src/auravlian/presentation/main_window.py`
- `src/auravlian/presentation/pages/base.py`
- `src/auravlian/presentation/pages/home.py`
- `src/auravlian/presentation/pages/now_playing.py`
- `src/auravlian/presentation/theme/styles.qss`
- `src/auravlian/presentation/viewmodels/player_vm.py`
- `src/auravlian/presentation/widgets/playback_bar.py`
- `README.md`, `CHANGELOG.md`

Added:

- `tests/unit/test_queue.py`
- `tests/unit/test_playback_service.py`
- `tests/integration/test_qt_playback.py`
- `tests/integration/test_device_errors.py`
- `tests/ui/test_playback_ui.py`
- `scripts/playback_smoke.py`
- `PHASE2_REPORT.md`

Generated media, screenshots and JSON are isolated under ignored `artifacts/`; tests generate media under pytest temporary directories, never the user's library.

## Commands executed and results

Run from `C:\projects\Auravlian` in PowerShell:

```powershell
git status --short
git diff --stat
git diff --check
git diff -- tests/ui/test_foundation.py tests/conftest.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --tb=short -o faulthandler_timeout=15
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/capture_preview.py
.\.venv\Scripts\python.exe scripts/playback_smoke.py --audible
.\.venv\Scripts\python.exe scripts/playback_smoke.py
```

Final validation: **58 tests passed**, no skips or warnings; Ruff passed; mypy passed across 63 source files; pip reported no broken requirements. The 58 comprise the original 17 and 41 added cases. Original foundation tests and fixtures have no diff. Visual previews at 1440×900 and 960×700 logical sizes were inspected on the host's 125% scaling.

### Real media evidence

Generated PCM WAV integration tests exercised actual Qt/FFmpeg decoding, advancing position, 3,000 ms duration, pause, seek, resume, Stop, volume/mute output properties, natural track transitions, repeat-one, corrupt-MP3-to-valid-WAV recovery, rapid source changes and immediate stop after seek/resume. Additional adapter tests simulate unavailable devices and directly trigger the timeout handler; they do not claim a physical unplug test.

The UI smoke script ran in muted and optional audible modes through **Speakers (Realtek(R) Audio)**. It reported Playing with duration 8,000 ms and advancing position 64 ms, Paused at 2,500 ms after seek, then Stopped at 0 ms. Actual Qt screenshots were captured and inspected. Audible mode requested unmuted low-level tone output; human listening/sound quality was not verified.

### Issues discovered and resolved

- Initial Qt signal forwarding failed because position/duration signals require 64-bit Qt signatures. The adapter now uses `qlonglong` signals/slots, with narrowly documented ignores for inaccurate PySide 6.8 stub signatures.
- The first real-media test hung in a synchronous native `QMediaPlayer.stop()` call immediately after pause/seek/resume. Diagnostic pytest runs used `-vv -s -o faulthandler_timeout=10` and `15`; hung runs were interrupted and are not counted as passing.
- Tested `pip index versions PySide6` and temporarily installed `PySide6==6.10.3`; that version reproduced the same hang. Restored `PySide6==6.8.3`, retaining the existing dependency pin. The fix uses queued signals connected directly to Qt native transport/source slots. The immediate-stop case and rapid switch/stop/reopen regression pass on the original pin without artificial sleeps masking the failure. This establishes the tested fix; the exact native/backend root cause is not claimed.

Qt thread-affinity implementation follows the [Qt signals/slots documentation](https://doc.qt.io/qtforpython-6.11/tutorials/basictutorial/signals_and_slots.html); transport semantics follow [QMediaPlayer documentation](https://doc.qt.io/qtforpython-6.8/PySide6/QtMultimedia/QMediaPlayer.html).

## Launch and limitations

```powershell
.\.venv\Scripts\python.exe main.py
```

Open local audio files from Home, Now Playing or File/Ctrl+O. The queue is session-only and replaces on selection; it is not a persistent music library. Titles use filenames. Shuffle is intentionally reproducible with fixed seed 0 and repeats the same order per cycle. Seeking is enabled only for seekable media. Previous restarts after three seconds, otherwise moves backward.

WAV decoding and the available Realtek output were exercised. All MP3/FLAC/AAC/Ogg variants, physical disconnect/reconnect, human audible quality, clean Windows machines and additional DPI settings remain manual verification work. No installer/executable build or Phase 3 feature is claimed. README contains the physical-device/codec checklist.

Phase 2 stops here. Phase 3 requires user approval.
