"""Reproducible native Qt release smoke check, also used by the frozen executable."""

import json
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from photonguard.gui import MainWindow


def run(output_dir):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    checks = []
    expected = ["no_anomaly_detected", "likely_condition", "likely_condition", "ambiguous", "ambiguous"]
    conditions = [None, "saturation_clipping", "electronic_noise_increase", "source_intensity_drift", "efficiency_degradation"]

    def capture(name, expected_status, condition=None):
        window.run_button.click()
        deadline = time.monotonic() + 30
        while window.worker is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(.01)
        if window.worker is not None:
            # Finish the bounded simulation/file operation before destroying Qt.
            window.worker.wait()
            app.processEvents()
            raise RuntimeError("Capture exceeded smoke-check timeout")
        if window.last_report is None or window.last_report.status != expected_status:
            raise RuntimeError(f"Unexpected result for {name}: {window.evidence.toPlainText()}")
        if condition and condition not in {f.condition for f in window.last_report.findings}:
            raise RuntimeError(f"Expected hypothesis not found for {name}")
        app.processEvents()
        if not window.grab().save(str(output_dir / f"{name}.png")):
            raise RuntimeError("Could not write screenshot")
        checks.append({"capture": name, "report": asdict(window.last_report)})

    try:
        for index, name in enumerate(["healthy", "clipping", "electronic_noise", "source_drift", "efficiency_degradation"]):
            window.preset.setCurrentIndex(index)
            capture(name, expected[index], conditions[index])
        with TemporaryDirectory(prefix="photonguard-smoke-") as directory:
            file = Path(directory) / "arbitrary.csv"
            file.write_text("# unit=arbitrary\n# bin_duration_s=0.001\nvalue\n" + "2\n" * 300)
            window.source.setCurrentIndex(1)
            window.csv_path.setText(str(file))
            capture("recorded_csv", "insufficient_evidence")
        result = {"qt_platform": app.platformName(), "checks": checks}
        (output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    finally:
        window.close()
        QCoreApplication.processEvents()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    print(run(parser.parse_args().output_dir))
