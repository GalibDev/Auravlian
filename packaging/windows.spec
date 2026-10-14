from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH).parent
data = collect_data_files('auravlian') + [(str(root / 'THIRD_PARTY_NOTICES.md'), '.')]
data += [(str(path), 'licenses') for path in (root / 'packaging/licenses').glob('*')]
analysis = Analysis([str(root / 'main.py')], pathex=[str(root / 'src')],
                    datas=data,
                    hiddenimports=collect_submodules('mutagen'),
                    excludes=['tkinter', 'matplotlib', 'pytest', 'PySide6.QtWebEngineCore'])
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True,
          name='Auravlian', console=False, icon=str(root / 'assets/logo/auravlian.ico'))
distribution = COLLECT(exe, analysis.binaries, analysis.datas, name='Auravlian')

