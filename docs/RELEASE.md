# Windows build and validation

Use Windows x64 and Python 3.12.10 to reproduce the verified environment.
`requirements-windows.txt` records the tested dependency snapshot; it is not a
promise of byte-identical binaries or random streams across other environments.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
.\.venv\Scripts\python.exe -m pip install -e ".[gui,test,build]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe packaging\build_windows.py
```

The output is `dist/PhotonGuard/PhotonGuard.exe`. Keep the entire PhotonGuard
directory together, including `_internal`, source, documentation, examples and
licenses. Launch the executable normally to open the desktop; Python need not
be separately installed on the target. Existing output is preserved: for a new
build use `--output-dir dist/candidate2`. Build output is ignored by Git.

PyInstaller's [one-directory Windows build](https://pyinstaller.org/en/stable/usage.html)
keeps native libraries visible and replaceable. No installer, administrator
privileges, auto-update service, network connection, or account is required by
the running application. This does not imply validation on every Windows release
or on a clean physical laboratory computer. The executable is unsigned.

## Native release smoke check

The default pytest UI tests are non-interactive (Qt offscreen). Separately run:

```powershell
.\.venv\Scripts\python.exe -m photonguard.smoke outputs/native-smoke
$process = Start-Process -FilePath (Resolve-Path dist/PhotonGuard/PhotonGuard.exe) -ArgumentList '--smoke-test', 'outputs/packaged-smoke' -WindowStyle Hidden -PassThru -Wait
$process.ExitCode
Get-Content outputs/packaged-smoke/result.json
```

The executable's `--smoke-test <output-directory>` validation mode exercises all
five presets and a synthetic arbitrary-unit CSV capture using the actual Qt
window, worker, plots and engine. It exits after writing screenshots and a JSON
result. Status mismatches or failures give a nonzero exit. Use an empty output
directory to avoid confusing previous evidence with a new run; it replaces files
with the same names. A normal launch does not run this check or export artifacts.

The smoke result must identify the `windows` Qt platform for a native check.
Inspect screenshots as well as exit status. Test from outside the checkout when
checking the packaged executable. Native pytest runs in the development desktop
produced Windows COM exception messages and one initial failed run; offscreen
tests and standalone native application checks are reported separately. The
underlying desktop/Qt exception cause has not been established.

## Scope of evidence

See [the acceptance and validation record](VALIDATION.md). A local executable
launch and synthetic checks do not establish deployment on other PCs, device
compatibility, physical calibration, quantum entropy or cryptographic security.
Real detector captures and live adapters require separate laboratory work.
The founder's deferred independent review remains a separate post-implementation
gate; self-review and successful packaging do not substitute for it.
