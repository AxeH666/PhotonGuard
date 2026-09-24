# Third-party components

PhotonGuard's own source is MIT-licensed. Dependency code, fonts and native
libraries retain their authors' licenses; MIT does not relicense them.
The build copies installed notices into `licenses/` and records versions in
`dependency-versions.txt`. Python's license is also included.

| Component | Upstream license / source |
| --- | --- |
| Python | [PSF and included notices](https://www.python.org/downloads/release/python-31210/) |
| NumPy | [BSD-3-Clause and bundled-library notices](https://github.com/numpy/numpy) |
| Matplotlib | [Matplotlib license and bundled font notices](https://github.com/matplotlib/matplotlib) |
| PySide6 / Shiboken / Qt | LGPLv3 option; see below |
| ContourPy, cycler, fonttools, kiwisolver, packaging, Pillow, pyparsing, python-dateutil, six | Licenses copied from installed distributions; versions are in the manifest |
| PyInstaller bootloader | [GPL with the bootloader distribution exception](https://pyinstaller.org/en/stable/license.html) |

## Qt and PySide

This application uses the open-source LGPLv3 option for Qt Core/Gui/Widgets,
the Qt Network/Svg dependencies collected by PyInstaller, and PySide6/Shiboken.
These libraries are copyright The Qt Company Ltd. and other
contributors. The official wheel metadata declares the LGPL/GPL alternatives;
the wheel's commercial-license text is not PhotonGuard's selected license.
Copies of LGPLv3, GPLv3 and Qt third-party attribution texts are in `licenses/`.

The portable build keeps Qt DLLs and PySide extensions dynamically loadable under
`_internal/`. It does not statically link or lock those libraries. Recipients may
replace them with compatible modified builds and may reverse-engineer/debug the
application for that purpose. PhotonGuard source and build instructions are
included so the application can also be rebuilt against modified libraries.

Corresponding upstream source and component notices for the verified 6.11.2 build:

- [PySide/Shiboken 6.11.2 source archives](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/).
- [Qt 6.11.2 source tree and submodule references](https://code.qt.io/cgit/qt/qt5.git/tree/?h=v6.11.2).
- [QtBase 6.11.2 source](https://code.qt.io/cgit/qt/qtbase.git/tree/?h=v6.11.2)
  and [third-party attribution](https://doc.qt.io/qt-6/qtcore-index.html#licenses-and-attributions).
- [Qt GUI attribution](https://doc.qt.io/qt-6/qtgui-index.html#licenses-and-attributions),
  [Qt for Python licenses](https://doc.qt.io/qtforpython-6/licenses.html), and
  [Qt's distribution obligations](https://www.qt.io/development/open-source-lgpl-obligations).

Keep licenses and source-access information with redistributed binaries. A build
with different dependency versions needs matching source links and notices.
The locally validated bundle is unsigned; no installer, signing service, or
third-party certification is supplied.
