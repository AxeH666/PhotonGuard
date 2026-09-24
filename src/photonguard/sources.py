"""One finite capture per read; no hardware transport or diagnostic logic."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from photonguard.csv_input import load_csv
from photonguard.detector import detector_response, linear_profile, sample_source
from photonguard.measurement import Measurement


class MeasurementSource(Protocol):
    def read(self) -> Measurement:
        """Return one validated capture, or raise; never return partial data."""
        ...


@dataclass(frozen=True)
class SimulationSource:
    rate_start: float = 10000
    rate_end: float = 10000
    efficiency_start: float = 1
    efficiency_end: float = 1
    noise_std: float = 0
    ceiling: float | None = None
    bin_duration_s: float = .001
    n_bins: int = 10000
    seed: int = 29

    def read(self) -> Measurement:
        """Repeat the seeded model; declare initial mean and zero baseline noise."""
        rng = np.random.default_rng(self.seed)
        incident = sample_source(linear_profile(self.rate_start, self.rate_end, self.n_bins),
                                 self.bin_duration_s, rng)
        output = detector_response(incident, rng,
            efficiency=linear_profile(self.efficiency_start, self.efficiency_end, self.n_bins),
            electronic_noise_std=self.noise_std, saturation_level=self.ceiling)
        return Measurement(output.readout, self.bin_duration_s, "count_equivalent",
            expected_mean=self.rate_start * self.efficiency_start * self.bin_duration_s,
            baseline_noise_std=0, saturation_level=self.ceiling)


@dataclass(frozen=True)
class CsvSource:
    path: str | Path
    metadata: dict | None = None

    def read(self) -> Measurement:
        return load_csv(self.path, metadata=self.metadata)
