"""Constant-rate Poisson illumination and an ideal photon counter.

Counts in non-overlapping bins are independent, with mean rate * duration.
The ideal detector records each incident photon once, without another draw.
"""

from math import isfinite
from numbers import Integral, Real

import numpy as np


def sample_photon_counts(
    rate_per_second: float,
    bin_duration_s: float,
    n_bins: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return a 1-D integer array of incident photon counts.

    Rate is finite and non-negative; duration is finite and strictly positive.
    n_bins is a positive integer. rng is a caller-owned NumPy Generator whose
    state advances on sampling. Unsupported numeric ranges raise ValueError.
    """
    for name, value in (
        ("rate_per_second", rate_per_second),
        ("bin_duration_s", bin_duration_s),
    ):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise ValueError(f"{name} must be a finite real number")
        try:
            finite = isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f"{name} must be a finite real number")
    if rate_per_second < 0:
        raise ValueError("rate_per_second must be non-negative")
    if bin_duration_s <= 0:
        raise ValueError("bin_duration_s must be positive")
    if isinstance(n_bins, (bool, np.bool_)) or not isinstance(n_bins, Integral):
        raise ValueError("n_bins must be a positive integer")
    if n_bins <= 0:
        raise ValueError("n_bins must be a positive integer")

    mean_count = float(rate_per_second) * float(bin_duration_s)
    if not isfinite(mean_count) or (rate_per_second > 0 and mean_count == 0):
        raise ValueError("rate * duration is outside the supported numeric range")

    # NumPy rejects means too close to the int64 limit; never clip those counts.
    return rng.poisson(lam=mean_count, size=int(n_bins))


def ideal_detect(incident_counts: np.ndarray) -> np.ndarray:
    """Copy a 1-D non-negative integer count array, preserving every count.

    An empty integer array is valid. No resampling, efficiency factor, gain,
    noise, or clipping is applied. The result does not alias the input.
    """
    counts = np.asarray(incident_counts)
    if counts.ndim != 1 or counts.dtype.kind not in "iu":
        raise ValueError("incident_counts must be a 1-D integer count array")
    if np.any(counts < 0):
        raise ValueError("incident_counts must be non-negative")
    return counts.copy()
