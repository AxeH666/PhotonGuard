"""Qt event-loop integration checks; no extra GUI testing framework."""

import os
import time
from pathlib import Path

import numpy as np
import pytest

# Deterministic, non-interactive tests. Native Windows smoke checks are separate.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from photonguard.gui import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    widget = MainWindow()
    widget.show()
    yield widget
    if widget.worker:
        widget.worker.wait(10000)
        app.processEvents()
    widget.close()
    widget.deleteLater()
    app.processEvents()


def capture(window, app):
    window.run_button.click()
    deadline = time.monotonic() + 10
    while window.worker is not None and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert window.worker is None, "Capture did not finish"
    app.processEvents()
    assert window.controls.isEnabled()


@pytest.mark.parametrize("preset,condition,status", [
    (0, None, "no_anomaly_detected"),
    (1, "saturation_clipping", "likely_condition"),
    (2, "electronic_noise_increase", "likely_condition"),
    (3, "source_intensity_drift", "ambiguous"),
    (4, "efficiency_degradation", "ambiguous"),
])
def test_presets_produce_evidence(window, app, preset, condition, status):
    window.preset.setCurrentIndex(preset)
    capture(window, app)
    assert window.last_report.status == status
    if condition:
        assert condition in [f.condition for f in window.last_report.findings]
        assert "(hypothesis)" in window.evidence.toPlainText()
    assert "not proof" in window.evidence.toPlainText()
    assert len(window.figure.axes) == 2
    line = window.figure.axes[0].lines[0]
    assert len(line.get_xdata()) == 2000
    assert line.get_xdata()[0] == .0005
    assert sum(bar.get_height() for bar in window.figure.axes[1].patches) == pytest.approx(1)


def test_csv_capture_and_bad_file_clear_old_results(window, app, tmp_path):
    window.source.setCurrentIndex(1)
    window.csv_path.setText(str(Path("examples/data/synthetic_counts.csv").resolve()))
    capture(window, app)
    assert window.last_measurement.values.size == 512
    assert window.last_report.status == "no_anomaly_detected"
    assert "CSV capture" in window.evidence.toPlainText()
    window.csv_path.setText(str(tmp_path / "missing.csv"))
    capture(window, app)
    assert window.last_report is None
    assert window.figure.axes == []
    assert "could not be analyzed" in window.status.text()


def test_csv_missing_metadata_can_be_supplied(window, app, tmp_path):
    file = tmp_path / "capture.csv"
    file.write_text("value\n" + "2\n" * 300)
    window.source.setCurrentIndex(1)
    window.csv_path.setText(str(file))
    window.csv_unit.setCurrentText("arbitrary")
    window.csv_fields["bin_duration_s"].setText("0.001")
    capture(window, app)
    assert window.last_report.status == "insufficient_evidence"
    assert window.last_measurement.expected_mean is None
    window.csv_fields["bin_duration_s"].setText("invalid")
    capture(window, app)
    assert window.last_measurement is None
    assert "convert" in window.evidence.toPlainText()


def test_seed_repeatability_and_short_capture(window, app):
    window.bins.setValue(100)
    capture(window, app)
    first = window.last_measurement.values.copy()
    capture(window, app)
    np.testing.assert_array_equal(first, window.last_measurement.values)
    assert window.last_report.status == "insufficient_evidence"


def test_close_waits_for_active_worker(window, app):
    window.run_button.click()
    assert window.worker is not None
    window.close()
    assert window.isVisible()
    deadline = time.monotonic() + 10
    while window.worker is not None and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)
    assert window.worker is None


def test_plot_error_preserves_diagnostic_evidence(window, app, monkeypatch):
    def cannot_plot(measurement):
        raise ValueError("unsupported numeric range")
    monkeypatch.setattr(window, "render_plots", cannot_plot)
    capture(window, app)
    assert window.last_report.status == "no_anomaly_detected"
    assert "Plots unavailable" in window.evidence.toPlainText()
    assert "not proof" in window.evidence.toPlainText()
