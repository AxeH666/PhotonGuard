"""Strict recorded-data input; no simulation or diagnostic rules here."""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from photonguard.measurement import Measurement

MAX_SAMPLES = 1_000_000
MAX_BYTES = 32 * 1024 * 1024
FIELDS = {"unit", "bin_duration_s", "expected_mean", "baseline_noise_std", "saturation_level"}


def load_csv(path: str | Path, *, metadata: dict | None = None) -> Measurement:
    """Read a complete UTF-8 capture, with optional missing metadata supplied by caller.

    Caller metadata may supplement file metadata but cannot contradict it.
    Comment metadata precedes the header: '# key=value'. No calibration is guessed.
    """
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("CSV exceeds the 32 MiB capture limit")
    supplied = {} if metadata is None else dict(metadata)
    if set(supplied) - FIELDS:
        raise ValueError("Unknown metadata fields: " + ", ".join(sorted(set(supplied) - FIELDS)))
    file_metadata = {}
    values, times = [], []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        for header in stream:
            if not header.strip():
                continue
            if not header.lstrip().startswith("#"):
                break
            comment = header.lstrip()[1:].strip()
            if "=" not in comment:
                continue
            key, value = (part.strip() for part in comment.split("=", 1))
            if key not in FIELDS or key in file_metadata:
                raise ValueError(f"Unknown or duplicate CSV metadata: {key}")
            file_metadata[key] = value
        else:
            raise ValueError("CSV has no header or measurements")

        for key, value in file_metadata.items():
            if key != "unit":
                try:
                    value = float(value)
                except ValueError as error:
                    raise ValueError(f"Invalid numeric metadata: {key}") from error
            if key in supplied and supplied[key] != value:
                raise ValueError(f"Conflicting metadata: {key}")
            supplied[key] = value
        if not {"unit", "bin_duration_s"} <= supplied.keys():
            raise ValueError("Declare unit and bin_duration_s in the CSV or import metadata")
        try:
            reader = csv.reader(stream, strict=True)
            columns = next(csv.reader([header], strict=True))
            if columns not in (["value"], ["value", "time_s"], ["time_s", "value"]):
                raise ValueError("CSV header must be value, optionally with time_s")
            value_index = columns.index("value")
            time_index = columns.index("time_s") if "time_s" in columns else None
            for row_number, row in enumerate(reader, start=1):
                if len(row) != len(columns) or any(not cell.strip() for cell in row):
                    raise ValueError(f"CSV data row {row_number} has missing or extra fields")
                if len(values) >= MAX_SAMPLES:
                    raise ValueError("CSV exceeds the 1,000,000 sample limit")
                try:
                    if supplied["unit"] == "counts":
                        exact = Decimal(row[value_index])
                        if not exact.is_finite() or exact != exact.to_integral_value() or abs(exact) > 2**53:
                            raise ValueError("Count is fractional, non-finite, or exceeds exact float integer range")
                    values.append(float(row[value_index]))
                    if time_index is not None:
                        times.append(float(row[time_index]))
                except (ValueError, InvalidOperation) as error:
                    raise ValueError(f"CSV data row {row_number} is invalid for its declared unit") from error
        except csv.Error as error:
            raise ValueError(f"Malformed CSV: {error}") from error

    measurement = Measurement(values, **supplied)
    if times:
        intervals = np.diff(times)
        dt = measurement.bin_duration_s
        if not np.isfinite(times).all() or np.any(intervals <= 0) or not np.allclose(intervals, dt, rtol=1e-6, atol=dt * 1e-9):
            raise ValueError("time_s must be finite, increasing, and uniformly spaced by bin_duration_s")
    return measurement
