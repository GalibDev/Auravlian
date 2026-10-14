# Third-party runtime components

Auravlian bundles Python 3.12, PySide6/Qt 6.8.3, Shiboken 6.8.3, NumPy 2.2.6, Mutagen 1.47.0 and the FFmpeg libraries supplied with Qt Multimedia. Original upstream notices for Qt's LGPL, Mutagen and NumPy are included under `licenses/` in the distribution. Qt/FFmpeg remain separate shared DLLs in `_internal`.

Upstream sources and terms:

- Python: https://www.python.org/downloads/source/ and https://docs.python.org/3/license.html
- Qt 6.8.3: https://download.qt.io/archive/qt/6.8/6.8.3/ and https://doc.qt.io/qt-6.8/licenses-used-in-qt.html
- PySide/Shiboken 6.8.3: https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.8.3 and https://doc.qt.io/qtforpython-6.8/licenses.html
- Mutagen: https://github.com/quodlibet/mutagen/tree/release-1.47.0
- NumPy/OpenBLAS: https://numpy.org/doc/2.2/license.html and the included NumPy license text.
- FFmpeg: https://ffmpeg.org/legal.html and https://code.qt.io/cgit/qt/qtmultimedia.git/tree/src/3rdparty/ffmpeg?h=v6.8.3
- PyInstaller bootloader: https://pyinstaller.org/en/stable/license.html

Auravlian source and pinned rebuild instructions: https://github.com/GalibDev/Auravlian. User-supplied logo artwork is preserved; no grant to reuse that branding is implied by these dependency notices.
