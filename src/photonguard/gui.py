"""Finite-capture desktop UI. Physics and diagnostic rules live elsewhere."""

import sys

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QScrollArea, QSpinBox, QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from photonguard.diagnostics import analyze
from photonguard.sources import CsvSource, MeasurementSource, SimulationSource


class CaptureWorker(QThread):
    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, source: MeasurementSource, parent):
        super().__init__(parent)
        self.source = source

    def run(self):
        try:
            measurement = self.source.read()
            self.succeeded.emit(measurement, analyze(measurement))
        except Exception as exc:
            self.failed.emit(str(exc))


def number(value, maximum, *, minimum=0, decimals=4):
    control = QDoubleSpinBox()
    control.setDecimals(decimals)
    control.setRange(minimum, maximum)
    control.setValue(value)
    return control


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotonGuard — photon detector measurement screening")
        self.resize(1280, 850)
        self.worker = None
        self.last_measurement = self.last_report = None
        self.capture_description = ""

        self.source = QComboBox()
        self.source.addItems(["Simulation", "Recorded CSV"])
        self.inputs = QTabWidget()
        self.inputs.tabBar().hide()
        self.source.currentIndexChanged.connect(self.inputs.setCurrentIndex)
        simulation = QWidget()
        form = QFormLayout(simulation)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.preset = QComboBox()
        self.preset.addItems(["Healthy baseline", "Saturation / clipping", "Electronic noise",
                              "Source-intensity drift", "Efficiency degradation"])
        form.addRow("Scenario preset", self.preset)
        self.rate_start = number(10000, 1e7)
        self.rate_end = number(10000, 1e7)
        self.efficiency_start = number(1, 1)
        self.efficiency_end = number(1, 1)
        self.noise = number(0, 1000)
        self.clip = QCheckBox("Apply upper readout limit")
        self.ceiling = number(8, 1e7, minimum=0.0001)
        self.ceiling.setEnabled(False)
        self.clip.toggled.connect(self.ceiling.setEnabled)
        self.duration = number(.001, 10, minimum=.000001, decimals=6)
        self.bins = QSpinBox()
        self.bins.setRange(1, 100000)
        self.bins.setValue(10000)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(29)
        for label, control in [("Initial rate (photons/s)", self.rate_start),
                ("Final rate (photons/s)", self.rate_end),
                ("Initial efficiency (0–1)", self.efficiency_start),
                ("Final efficiency (0–1)", self.efficiency_end),
                ("Read-noise std (count eq.)", self.noise), ("", self.clip),
                ("Upper limit (count eq.)", self.ceiling), ("Bin duration (s)", self.duration),
                ("Number of bins", self.bins), ("Pseudorandom seed", self.seed)]:
            form.addRow(label, control)
        note = QLabel("Baseline assumption: initial rate × initial efficiency × bin duration; "
                      "zero baseline read noise. Presets change controls only. "
                      "Rates and efficiencies vary linearly between bin centres.")
        note.setWordWrap(True)
        form.addRow(note)
        self.preset.currentIndexChanged.connect(self.apply_preset)
        self.inputs.addTab(simulation, "Simulation")

        recorded = QWidget()
        csv_form = QFormLayout(recorded)
        self.csv_path = QLineEdit()
        self.csv_path.setPlaceholderText("Select a CSV capture")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.browse_csv)
        csv_form.addRow("File", self.csv_path)
        csv_form.addRow(browse)
        note = QLabel("Use file metadata or supply missing fields below. Conflicting values "
                      "are rejected. Blank fields do not assume a calibration.")
        note.setWordWrap(True)
        csv_form.addRow(note)
        self.csv_unit = QComboBox()
        self.csv_unit.addItems(["Use file metadata", "counts", "count_equivalent", "arbitrary"])
        csv_form.addRow("Unit", self.csv_unit)
        self.csv_fields = {}
        for key, label in [("bin_duration_s", "Bin duration (s)"),
                ("expected_mean", "Expected mean (value units)"),
                ("baseline_noise_std", "Baseline noise std"),
                ("saturation_level", "Known upper limit")]:
            field = QLineEdit()
            field.setPlaceholderText("Leave blank to use file metadata")
            csv_form.addRow(label, field)
            self.csv_fields[key] = field
        self.inputs.addTab(recorded, "Recorded CSV")

        self.run_button = QPushButton("Capture and analyze")
        self.run_button.clicked.connect(self.start_capture)
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.addWidget(QLabel("Measurement source"))
        controls_layout.addWidget(self.source)
        controls_layout.addWidget(self.inputs)
        controls_layout.addWidget(self.run_button)
        controls_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setMinimumWidth(355)
        self.controls = controls

        results = QWidget()
        layout = QVBoxLayout(results)
        self.status = QLabel("Ready — choose a source and capture measurements")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-size: 17px; font-weight: bold; padding: 6px;")
        layout.addWidget(self.status)
        self.figure = Figure(figsize=(8, 4), layout="constrained")
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(NavigationToolbar2QT(self.canvas, self))
        layout.addWidget(self.canvas, 3)
        self.evidence = QTextBrowser()
        self.evidence.setMinimumHeight(200)
        self.evidence.setPlainText("Results are screening hypotheses, not proof of physical hardware faults. "
                                   "Simulation cannot establish quantum entropy or cryptographic security.")
        layout.addWidget(self.evidence, 2)
        splitter = QSplitter()
        splitter.addWidget(scroll)
        splitter.addWidget(results)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 920])
        self.setCentralWidget(splitter)

    def apply_preset(self, index):
        self.rate_start.setValue(10000)
        self.rate_end.setValue(5000 if index == 3 else 10000)
        self.efficiency_start.setValue(1)
        self.efficiency_end.setValue(.5 if index == 4 else 1)
        self.noise.setValue(4 if index == 2 else 0)
        self.clip.setChecked(index == 1)
        self.ceiling.setValue(8)
        self.duration.setValue(.001)
        self.bins.setValue(10000)
        self.seed.setValue(29)

    def browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open recorded measurements", "", "CSV (*.csv)")
        if path:
            self.csv_path.setText(path)

    def start_capture(self):
        if self.worker is not None:
            return
        self.last_measurement = self.last_report = None
        self.figure.clear()
        self.canvas.draw_idle()
        self.evidence.clear()
        try:
            if self.source.currentIndex() == 0:
                parameters = dict(rate_start=self.rate_start.value(), rate_end=self.rate_end.value(),
                    efficiency_start=self.efficiency_start.value(), efficiency_end=self.efficiency_end.value(),
                    noise_std=self.noise.value(), ceiling=self.ceiling.value() if self.clip.isChecked() else None,
                    bin_duration_s=self.duration.value(), n_bins=self.bins.value(), seed=self.seed.value())
                source = SimulationSource(**parameters)
                self.capture_description = f"Simulated capture; seed {parameters['seed']}. Pseudorandom model output."
            else:
                metadata = {key: float(field.text()) for key, field in self.csv_fields.items() if field.text().strip()}
                if self.csv_unit.currentIndex():
                    metadata["unit"] = self.csv_unit.currentText()
                path = self.csv_path.text()
                source = CsvSource(path, metadata)
                self.capture_description = f"CSV capture: {path}. Metadata is supplied, not independently verified."
        except ValueError as exc:
            self.show_error(str(exc))
            return
        self.controls.setEnabled(False)
        self.status.setText("Reading measurements and analyzing…")
        self.worker = CaptureWorker(source, self)
        self.worker.succeeded.connect(self.show_result)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.capture_finished)
        self.worker.start()

    def capture_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.controls.setEnabled(True)

    def show_error(self, message):
        self.last_measurement = self.last_report = None
        self.status.setText("Capture could not be analyzed")
        self.evidence.setPlainText(message)

    def show_result(self, measurement, report):
        self.last_measurement, self.last_report = measurement, report
        self.status.setText(report.status.replace("_", " ").capitalize())
        lines = [self.capture_description,
            f"Analyzed {measurement.values.size} bins; dt = {measurement.bin_duration_s:g} s; unit = {measurement.unit}.",
            f"Declared baseline mean: {measurement.expected_mean}; noise std: {measurement.baseline_noise_std}; ceiling: {measurement.saturation_level}.",
            "", "OBSERVED EVIDENCE"]
        for finding in report.findings:
            lines.extend([finding.condition.replace("_", " ").capitalize() + " (hypothesis)",
                          finding.evidence, "Other explanations: " + finding.alternatives, ""])
        if not report.findings:
            lines.append("No condition identified by the applicable screening rules.")
        lines.extend(["", "LIMITATIONS", *report.limitations])
        lines.extend(["", "METRICS (definitions: docs/DIAGNOSTICS.md)"])
        for name, value in report.metrics.items():
            lines.append(f"{name}: {value:.6g}" if value is not None else f"{name}: unavailable")
        self.evidence.setPlainText("\n".join(lines))
        try:
            self.render_plots(measurement)
        except (ValueError, OverflowError, IndexError) as exc:
            self.figure.clear()
            self.canvas.draw_idle()
            self.evidence.append("\nPlots unavailable for this numeric range: " + str(exc))

    def render_plots(self, measurement):
        self.figure.clear()
        time_axes, histogram = self.figure.subplots(2, 1)
        x = measurement.values
        shown = min(x.size, 2000)
        time_axes.plot((np.arange(shown) + .5) * measurement.bin_duration_s, x[:shown], linewidth=.7)
        if measurement.expected_mean is not None:
            time_axes.axhline(measurement.expected_mean, color="tab:orange", linestyle="--", label="Declared baseline mean")
            time_axes.legend(fontsize=8)
        time_axes.set(title=f"Readout vs time — first {shown:,} of {x.size:,} bins",
                      xlabel="Elapsed bin-centre time (s)", ylabel=measurement.unit)
        # Probability per displayed histogram interval, not density or a Poisson PMF.
        histogram.hist(x, bins=min(60, max(1, int(np.sqrt(x.size)))),
                       weights=np.full(x.size, 1 / x.size), color="tab:blue")
        histogram.set(title="Measured distribution — all bins", xlabel=measurement.unit,
                      ylabel="Probability / interval")
        self.canvas.draw()

    def closeEvent(self, event):
        if self.worker is not None:
            event.ignore()
            self.status.setText("Capture in progress — close after it finishes")
        else:
            event.accept()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
