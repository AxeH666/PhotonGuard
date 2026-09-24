import numpy as np
import pytest

from examples.scenarios import generate, scenarios
from photonguard.csv_input import load_csv
from photonguard.diagnostics import analyze
from photonguard.measurement import Measurement
from photonguard.sources import SimulationSource


@pytest.mark.parametrize("mean", [.1, 1, 10, 100])
@pytest.mark.parametrize("efficiency", [.2, .8])
@pytest.mark.parametrize("noise", [0, 2])
@pytest.mark.parametrize("seed", [7, 29])
def test_healthy_declared_baselines_across_representative_ranges(mean, efficiency, noise, seed):
    rate = mean / (.001 * efficiency)
    data = SimulationSource(rate_start=rate, rate_end=rate,
        efficiency_start=efficiency, efficiency_end=efficiency, noise_std=noise, seed=seed).read()
    # An established nonzero healthy noise floor must be supplied, not inferred.
    calibrated = Measurement(data.values, .001, "count_equivalent", mean, noise)
    report = analyze(calibrated)
    assert report.status == "no_anomaly_detected"
    assert not report.findings


def test_reproducible_csv_examples_match_simulation_reports(tmp_path):
    reports = generate(tmp_path)
    conditions = {"healthy": None, "clipping": "saturation_clipping",
        "electronic_noise": "electronic_noise_increase", "source_drift": "source_intensity_drift",
        "efficiency_degradation": "efficiency_degradation"}
    for name, source in scenarios().items():
        imported = load_csv(tmp_path / f"{name}.csv")
        np.testing.assert_array_equal(source.read().values, imported.values)
        report = analyze(imported)
        assert report == analyze(source.read())
        assert reports[name]["status"] == report.status
        if conditions[name]:
            assert conditions[name] in {f.condition for f in report.findings}
        else:
            assert report.status == "no_anomaly_detected"
