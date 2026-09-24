import numpy as np
import pytest

from photonguard.detector import detector_response, linear_profile, sample_source
from photonguard.diagnostics import analyze
from photonguard.measurement import Measurement


def capture(seed=10, end_rate=10_000, end_efficiency=1, noise=0, ceiling=None):
    rng = np.random.default_rng(seed)
    incident = sample_source(linear_profile(10_000, end_rate, 10_000), 0.001, rng)
    values = detector_response(incident, rng, efficiency=linear_profile(1, end_efficiency, 10_000),
                               electronic_noise_std=noise, saturation_level=ceiling).readout
    return Measurement(values, 0.001, "count_equivalent", 10, 0, ceiling)


@pytest.mark.parametrize("seed", [1, 7, 19, 42])
def test_healthy_baseline_has_no_findings(seed):
    report = analyze(capture(seed))
    assert report.status == "no_anomaly_detected"
    assert not report.findings


@pytest.mark.parametrize("kwargs,expected", [
    ({"ceiling": 6}, {"saturation_clipping"}),
    ({"noise": 5}, {"electronic_noise_increase"}),
    ({"end_rate": 30_000}, {"source_intensity_drift"}),
    ({"end_efficiency": 0.2}, {"source_intensity_drift", "efficiency_degradation"}),
])
def test_four_scenarios_have_evidence_and_qualified_inference(kwargs, expected):
    report = analyze(capture(**kwargs))
    assert expected <= {f.condition for f in report.findings}
    assert all(f.evidence and f.alternatives for f in report.findings)
    if "efficiency_degradation" in expected:
        assert report.status == "ambiguous"


def test_clipping_and_trend_do_not_masquerade_as_stationary_electronic_noise():
    for data in [capture(ceiling=6, noise=10), capture(end_rate=100_000)]:
        assert "electronic_noise_increase" not in {f.condition for f in analyze(data).findings}


def test_missing_metadata_short_and_zero_captures_abstain():
    assert analyze(Measurement([1, 2], 1, "counts")).status == "insufficient_evidence"
    data = capture()
    assert analyze(Measurement(data.values, 1, "count_equivalent")).status == "insufficient_evidence"
    assert analyze(Measurement(np.zeros(1000), 1, "counts", 0, 0)).status == "insufficient_evidence"


def test_arbitrary_units_do_not_get_poisson_noise_or_efficiency_diagnosis():
    for data in (capture(noise=20), capture(end_efficiency=0.2)):
        report = analyze(Measurement(data.values, 1, "arbitrary", 10, 0))
        assert not {"electronic_noise_increase", "efficiency_degradation"} & {f.condition for f in report.findings}


def test_overflowing_noise_metadata_does_not_produce_a_healthy_result():
    with pytest.raises(ValueError, match="noise variance"):
        analyze(Measurement(capture().values, 1, "count_equivalent", 10, 1e308))


def test_known_nonclipping_integer_ceiling_does_not_flag_natural_poisson_mass():
    values = np.random.default_rng(23).poisson(0.1, 10_000)
    # At this seed no count exceeds 3; ordinary mass at 3 is not clipping.
    report = analyze(Measurement(values, 1, "counts", 0.1, 0, 3))
    assert report.status == "no_anomaly_detected"


def test_bad_ceiling_context_abstains():
    report = analyze(Measurement(np.full(1000, 5), 1, "counts", 5, 0, 2))
    assert report.status == "insufficient_evidence"
    assert "exceed" in " ".join(report.limitations)


def test_input_is_copied_and_read_only():
    values = np.array([0, 1, 2])
    data = Measurement(values, 1, "counts")
    values[0] = 10
    assert data.values[0] == 0
    with pytest.raises(ValueError):
        data.values[0] = 10


@pytest.mark.parametrize("values,unit", [([], "counts"), ([np.nan], "counts"),
    ([1.5], "counts"), ([-1], "counts"), ([[1]], "counts"), ([1], "volts")])
def test_invalid_measurements(values, unit):
    with pytest.raises(ValueError):
        Measurement(values, 1, unit)
