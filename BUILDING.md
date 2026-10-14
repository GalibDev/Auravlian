# Windows builds — Auravlian 0.8.0

Python 3.12 x64, Windows 10/11, pinned runtime/dev/build dependencies and Inno Setup 6 are required for building. Built applications include Python and do not require a separate Python installation.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/build_icon.py
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm packaging/windows.spec
# Use your installed Inno Setup compiler path:
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' packaging\installer.iss
Compress-Archive -Path dist\Auravlian -DestinationPath dist\Auravlian-Portable-0.8.0-win64.zip -Force
```

This checkout used a per-user build compiler under `.tools\InnoSetup\ISCC.exe` and Inno Setup 6.7.3. Build logs/artifacts are ignored by Git. Branding icon generation crops the original symbol above the old wordmark, proportionally scales and pads it, and never redraws/recolors the symbol.

Outputs:

- `dist/Auravlian/Auravlian.exe` — portable folder entry point. Keep the entire folder together.
- `dist/Auravlian-Portable-0.8.0-win64.zip` — transferable portable folder.
- `dist/Auravlian-Setup-0.8.0.exe` — per-user installer; default `%LOCALAPPDATA%\Programs\Auravlian`.

## Runtime diagnostics

```powershell
.\.venv\Scripts\python.exe main.py --smoke-test artifacts\source-diagnostics
.\dist\Auravlian\Auravlian.exe --smoke-test C:\projects\Auravlian\artifacts\portable-diagnostics
```

Diagnostics generates muted PCM audio and a matching LRC file, uses isolated INI settings/database, exercises actual decoding, timing, pause/seek, history, lyrics and buffer capture, writes `result.json`/screenshot, then exits. Its log uses normal application logging. Inspect the JSON `result`; process exit alone is not proof of a passing smoke. A physical/default audio device must exist. No files in the user's music library are modified.

## Clean-machine release validation still required

On fresh Windows 10 and 11 VMs without Python/Qt: copy the installer, install as a normal user, check Start Menu/desktop shortcut choice, open real MP3/FLAC/AAC/Ogg/WAV files, switch output devices, disconnect/reconnect hardware, import a large library, close during scanning, test tray/mini/fullscreen/lyrics/M3U, restart and check persistence, then uninstall. Confirm music and user data survive. Repeat at 100%, 125%, 150% and 200% DPI. Inspect unsigned-build prompts and sign release binaries if distributing broadly. Host install/uninstall tests do not replace this VM/device matrix.

Qt shared DLLs and the multimedia plugin/FFmpeg DLLs are intentionally bundled. Dependency sources/notices are documented in `THIRD_PARTY_NOTICES.md` and `packaging/licenses/`.
