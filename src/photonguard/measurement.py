"""Small source-independent input used by the diagnostic engine."""

from dataclasses import dataclass
from numbers import Real

import numpy as np


@dataclass(frozen=True)
class Measurement:
    values: np.ndarray
    bin_duration_s: float
    unit: str
    expected_mean: float | None = None
    baseline_noise_std: float | None = None
    saturation_level: float | None = None

    def __post_init__(self):
        raw = np.asarray(self.values)
        if raw.dtype.kind not in "iuf":
            raise ValueError("Measurements must contain real numeric values, not strings, booleans, or complex numbers")
        if self.unit == "counts" and np.any(raw > 2**53):
            raise ValueError("Counts exceed the exact float integer range")
        values = np.array(raw, dtype=float, copy=True)
        if values.ndim != 1 or not values.size or not np.isfinite(values).all():
            raise ValueError("Measurements must be a nonempty finite 1-D array")
        if (isinstance(self.bin_duration_s, (bool, np.bool_)) or not isinstance(self.bin_duration_s, Real)
                or not np.isfinite(self.bin_duration_s) or self.bin_duration_s <= 0):
            raise ValueError("Bin duration must be finite and positive")
        if not np.isfinite(values.size * float(self.bin_duration_s)):
            raise ValueError("Capture duration exceeds supported numeric range")
        if self.unit not in {"counts", "count_equivalent", "arbitrary"}:
            raise ValueError("Unit must be counts, count_equivalent, or arbitrary")
        if self.unit == "counts" and (np.any(values < 0) or np.any(values != np.floor(values))):
            raise ValueError("Photon counts must be non-negative integers")
        for name in ("expected_mean", "baseline_noise_std", "saturation_level"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                                      or not np.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and non-negative when supplied")
        if self.saturation_level == 0:
            raise ValueError("Saturation level must be positive")
        values.setflags(write=False)
        object.__setattr__(self, "values", values)
