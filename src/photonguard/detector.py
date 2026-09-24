"""Binomial photodetection and a normalized noisy/clipped readout."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np

from photonguard.baseline import ideal_detect


def linear_profile(start: float, end: float, n_bins: int) -> np.ndarray:
    """Values at the first and last bin centres; one bin uses start."""
    if isinstance(n_bins, (bool, np.bool_)) or not isinstance(n_bins, Integral) or n_bins < 1:
        raise ValueError("n_bins must be a positive integer")
    if not np.isfinite([start, end]).all():
        raise ValueError("Profile endpoints must be finite")
    return np.linspace(start, end, n_bins)


def sample_source(rates_per_second, bin_duration_s: float, rng: np.random.Generator) -> np.ndarray:
    """Independent Poisson counts for a supplied piecewise-constant rate profile."""
    rates = np.asarray(rates_per_second, dtype=float)
    if rates.ndim != 1 or rates.size == 0 or not np.isfinite(rates).all() or np.any(rates < 0):
        raise ValueError("Source rates must be a nonempty finite non-negative 1-D array")
    if not np.isfinite(bin_duration_s) or bin_duration_s <= 0:
        raise ValueError("bin_duration_s must be finite and positive")
    with np.errstate(over="ignore", under="ignore"):
        means = rates * bin_duration_s
    if not np.isfinite(means).all() or np.any((rates > 0) & (means == 0)):
        raise ValueError("Source mean is outside the supported numeric range")
    return rng.poisson(means)


@dataclass(frozen=True)
class DetectorOutput:
    detected_counts: np.ndarray
    readout: np.ndarray


def detector_response(incident_counts, rng: np.random.Generator, *, efficiency=1.0,
                      electronic_noise_std: float = 0.0,
                      saturation_level: float | None = None) -> DetectorOutput:
    """Apply detection, Gaussian read noise, then upper clipping, in that order.

    efficiency is a scalar or one probability per bin. Readout uses normalized
    detected-photon-equivalent units, not volts; negative noise excursions remain.
    See docs/PHYSICS.md. Inputs are never modified.
    """
    incident = ideal_detect(incident_counts)
    if np.any(incident > np.iinfo(np.int64).max):
        raise ValueError("Incident counts exceed the supported integer range")
    eta = np.asarray(efficiency, dtype=float)
    if eta.ndim > 1 or (eta.ndim == 1 and eta.shape != incident.shape):
        raise ValueError("Efficiency must be scalar or match the incident count shape")
    if not np.isfinite(eta).all() or np.any((eta < 0) | (eta > 1)):
        raise ValueError("Efficiency must lie in [0, 1]")
    if not np.isfinite(electronic_noise_std) or electronic_noise_std < 0:
        raise ValueError("Noise standard deviation must be finite and non-negative")
    if saturation_level is not None and (not np.isfinite(saturation_level) or saturation_level <= 0):
        raise ValueError("Saturation level must be finite and positive")
    detected = rng.binomial(incident.astype(np.int64), eta)
    readout = detected.astype(float)
    if electronic_noise_std:
        readout += rng.normal(0, electronic_noise_std, size=incident.size)
    if not np.isfinite(readout).all():
        raise ValueError("Readout exceeded the supported numeric range")
    if saturation_level is not None:
        readout = np.minimum(readout, saturation_level)
    return DetectorOutput(detected, readout)
