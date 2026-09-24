"""Build a portable directory; preserve any existing output instead of deleting it."""

import argparse
import importlib.metadata as metadata
from pathlib import Path
import shutil
import subprocess
import sys


def build(output_dir):
    if sys.platform != "win32":
        raise SystemExit("Build the Windows application on Windows")
    root = Path(__file__).resolve().parents[1]
    output_dir = Path(output_dir).resolve()
    bundle = output_dir / "PhotonGuard"
    if bundle.exists():
        raise SystemExit("Output already exists; choose a new --output-dir to preserve that build")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--onedir", "--windowed", "--noupx",
        "--name", "PhotonGuard", "--specpath", str(root / "build"),
        "--workpath", str(root / "build"), "--distpath", str(output_dir),
        "--paths", str(root / "src"), str(root / "packaging/launcher.py")], cwd=root, check=True)
    for name in ["LICENSE", "README.md", "THIRD_PARTY_NOTICES.md", "requirements-windows.txt",
                 "AGENTS.md", "PhotonGuard_Project_Scope_v1.1.docx"]:
        shutil.copy2(root / name, bundle / name)
    for name in ["docs", "examples", "src", "tests", "packaging", "licenses"]:
        shutil.copytree(root / name, bundle / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
    shutil.copy2(root / "pyproject.toml", bundle / "pyproject.toml")
    # Preserve installed runtime notices, including nested third-party notices.
    packages = ["numpy", "matplotlib", "PySide6-Essentials", "shiboken6", "contourpy",
        "cycler", "fonttools", "kiwisolver", "packaging", "pillow", "pyparsing",
        "python-dateutil", "six", "pyinstaller"]
    manifest = []
    for name in packages:
        distribution = metadata.distribution(name)
        manifest.append(f"{name}=={distribution.version}")
        for file in distribution.files or []:
            if ".." in file.parts:
                continue
            if "licenses" in file.parts or any(word in file.name.lower() for word in ("license", "copying", "notice")):
                destination = bundle / "licenses" / name / file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(distribution.locate_file(file), destination)
    shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", bundle / "licenses/Python-LICENSE.txt")
    (bundle / "dependency-versions.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(bundle / "PhotonGuard.exe")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    build(parser.parse_args().output_dir)
