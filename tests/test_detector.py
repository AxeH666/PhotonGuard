import numpy as np
import pytest

from photonguard.detector import detector_response, linear_profile, sample_source


def test_efficiency_limits_and_stage_separation():
    incident = np.array([0, 1, 5, 100])
    before = incident.copy()
    result = detector_response(incident, np.random.default_rng(1), saturation_level=3)
    np.testing.assert_array_equal(result.detected_counts, incident)
    np.testing.assert_array_equal(result.readout, [0, 1, 3, 3])
    np.testing.assert_array_equal(incident, before)
    zero = detector_response(incident, np.random.default_rng(1), efficiency=0)
    assert not zero.detected_counts.any()
    assert not zero.readout.any()


def test_binomial_thinning_has_expected_poisson_moments():
    rng = np.random.default_rng(19)
    incident = sample_source(np.full(100_000, 20_000), 0.001, rng)
    result = detector_response(incident, rng, efficiency=0.4)
    assert np.all(result.detected_counts <= incident)
    assert abs(result.readout.mean() - 8) < 6 * np.sqrt(8 / incident.size)
    assert abs(result.readout.var(ddof=1) - 8) < 6 * np.sqrt(8 / incident.size + 128 / (incident.size - 1))


def test_noise_is_zero_mean_and_adds_variance_without_changing_counts():
    rng = np.random.default_rng(20)
    incident = np.full(100_000, 10, dtype=int)
    result = detector_response(incident, rng, electronic_noise_std=3)
    np.testing.assert_array_equal(result.detected_counts, incident)
    assert abs(result.readout.mean() - 10) < 6 * 3 / np.sqrt(incident.size)
    assert abs(result.readout.var(ddof=1) - 9) < 6 * 9 * np.sqrt(2 / (incident.size - 1))
    noise_only = detector_response(np.zeros(1000, dtype=int), rng, electronic_noise_std=1)
    assert noise_only.readout.min() < 0


def test_drift_and_efficiency_degradation_are_distinct_stages():
    rng = np.random.default_rng(21)
    rates = linear_profile(100_000, 200_000, 10_000)
    incident = sample_source(rates, 0.001, rng)
    assert incident[-1000:].mean() > 1.7 * incident[:1000].mean()
    constant = sample_source(np.full(10_000, 100_000), 0.001, rng)
    result = detector_response(constant, rng, efficiency=linear_profile(1, 0.2, 10_000))
    assert result.detected_counts[-1000:].mean() < 0.4 * result.detected_counts[:1000].mean()
    np.testing.assert_array_equal(linear_profile(2, 8, 3), [2, 5, 8])
    np.testing.assert_array_equal(linear_profile(2, 8, 1), [2])


@pytest.mark.parametrize("kwargs", [
    {"efficiency": -0.1}, {"efficiency": 1.1}, {"efficiency": np.nan},
    {"efficiency": [0.5]}, {"efficiency": [[0.5, 0.5]]},
    {"electronic_noise_std": -1}, {"electronic_noise_std": np.inf},
    {"saturation_level": 0}, {"saturation_level": np.nan},
])
def test_invalid_detector_parameters(kwargs):
    with pytest.raises(ValueError):
        detector_response(np.array([1, 2]), np.random.default_rng(1), **kwargs)


@pytest.mark.parametrize("rates,dt", [([], 1), ([-1], 1), ([np.nan], 1),
    ([[1]], 1), ([1], 0), ([1], np.inf), ([1e308], 100), ([1e-300], 1e-300)])
def test_invalid_source_parameters(rates, dt):
    with pytest.raises(ValueError):
        sample_source(rates, dt, np.random.default_rng(1))


@pytest.mark.parametrize("n", [0, -1, True, 1.5])
def test_invalid_profile_length(n):
    with pytest.raises(ValueError):
        linear_profile(1, 2, n)
