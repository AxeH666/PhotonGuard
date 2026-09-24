import numpy as np
import pytest

from photonguard.baseline import ideal_detect, sample_photon_counts


@pytest.mark.parametrize("rate", [-1, np.nan, np.inf, -np.inf, True, "10", None, 10**400])
def test_invalid_rate(rate):
    with pytest.raises(ValueError, match="rate_per_second"):
        sample_photon_counts(rate, 0.001, 10, np.random.default_rng(1))


@pytest.mark.parametrize("duration", [0, -1, np.nan, np.inf, -np.inf, True, "1", None, 10**400])
def test_invalid_duration(duration):
    with pytest.raises(ValueError, match="bin_duration_s"):
        sample_photon_counts(10, duration, 10, np.random.default_rng(1))


@pytest.mark.parametrize("n_bins", [0, -1, 1.5, 2.0, True, np.bool_(False), "10", None])
def test_invalid_bin_count(n_bins):
    with pytest.raises(ValueError, match="n_bins"):
        sample_photon_counts(10, 0.001, n_bins, np.random.default_rng(1))


@pytest.mark.parametrize("rate,duration", [(1e308, 10), (1e-300, 1e-300), (1e20, 1)])
def test_unsupported_mean(rate, duration):
    with pytest.raises(ValueError):
        sample_photon_counts(rate, duration, 10, np.random.default_rng(1))


def test_output_contract_and_zero_rate():
    for rate in (0, 10_000):
        counts = sample_photon_counts(rate, 0.001, np.int64(100), np.random.default_rng(1))
        assert counts.shape == (100,)
        assert np.issubdtype(counts.dtype, np.integer)
        assert np.all(counts >= 0)
        if rate == 0:
            np.testing.assert_array_equal(counts, np.zeros(100, dtype=int))
    assert sample_photon_counts(1, 1, 1, np.random.default_rng(1)).shape == (1,)


def test_rate_duration_conversion_and_reproducibility():
    expected = np.random.default_rng(42).poisson(lam=10, size=100)
    for rate, duration in ((10_000, 0.001), (20_000, 0.0005), (10, 1)):
        actual = sample_photon_counts(rate, duration, 100, np.random.default_rng(42))
        np.testing.assert_array_equal(actual, expected)


def test_supplied_generator_advances_without_global_rng_changes():
    rng = np.random.default_rng(42)
    reference = np.random.default_rng(42)
    global_before = np.random.get_state()
    for _ in range(2):
        actual = sample_photon_counts(10, 1, 100, rng)
        np.testing.assert_array_equal(actual, reference.poisson(10, size=100))
    global_after = np.random.get_state()
    for before, after in zip(global_before, global_after):
        np.testing.assert_equal(before, after)


def test_ideal_detector_preserves_counts_without_aliasing():
    incident = np.array([0, 1, 2, 50, 10_000], dtype=np.int64)
    detected = ideal_detect(incident)
    np.testing.assert_array_equal(detected, incident)
    assert detected.dtype == incident.dtype
    assert not np.shares_memory(detected, incident)
    detected[0] = 9
    assert incident[0] == 0
    assert ideal_detect(np.array([], dtype=int)).shape == (0,)


@pytest.mark.parametrize("counts", [
    [-1, 1], [0.0, 1.0], [0.5, 1.5], [True, False], [[0, 1]], 1,
    [np.nan], [np.inf], ["1"],
])
def test_ideal_detector_rejects_invalid_counts(counts):
    with pytest.raises(ValueError, match="incident_counts"):
        ideal_detect(counts)


@pytest.mark.parametrize("mean", [0.1, 1.0, 10.0, 100.0])
def test_seeded_poisson_mean_and_variance(mean):
    n_bins = 100_000
    counts = ideal_detect(sample_photon_counts(
        mean / 0.001, 0.001, n_bins, np.random.default_rng(20260924)
    ))
    # Exact sampling standard errors for iid Poisson counts and unbiased S^2.
    mean_se = np.sqrt(mean / n_bins)
    variance_se = np.sqrt(mean / n_bins + 2 * mean**2 / (n_bins - 1))
    assert abs(counts.mean() - mean) <= 6 * mean_se
    assert abs(counts.var(ddof=1) - mean) <= 6 * variance_se


def test_poisson_zero_count_probability():
    # One simple distribution sanity check: P(N=0) = exp(-mean).
    n_bins = 100_000
    counts = sample_photon_counts(1, 1, n_bins, np.random.default_rng(123))
    probability = np.exp(-1)
    standard_error = np.sqrt(probability * (1 - probability) / n_bins)
    assert abs(np.mean(counts == 0) - probability) <= 6 * standard_error
