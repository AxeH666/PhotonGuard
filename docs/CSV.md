# Recorded CSV input

Use UTF-8 (with or without BOM), comma separators, a header `value`, and one
measurement per row. Optional `time_s` may be before or after `value`. No other
columns are accepted. Metadata comments precede the header:

```csv
# Example only; these three bins are too short for diagnostic screening
# unit=counts
# bin_duration_s=0.001
# expected_mean=10
# baseline_noise_std=0
value,time_s
9,0.000
12,0.001
8,0.002
```

`unit` and `bin_duration_s` are required. Optional metadata is `expected_mean`,
`baseline_noise_std`, and `saturation_level`. Their values are defined in
[diagnostic interpretation](DIAGNOSTICS.md), not inferred from the filename or
measured data. Numeric metadata must be finite; optional values should be omitted
when unknown, not written as zero or an empty string. Zero noise is an explicit
noiseless-baseline assumption. Duplicate or unknown metadata keys are errors.
Plain comment lines without `=` may describe provenance but are never evidence
used by diagnostics. Do not encode fault labels as metadata.

For a CSV without metadata comments, the Python call
`load_csv(path, metadata={"unit": "arbitrary", "bin_duration_s": 0.001})`
supplies known import context. Additional baseline metadata is optional. Caller
fields cannot contradict the file; conflicts are errors rather than overrides.

Units:

- `counts`: non-negative integer detected photon counts per bin.
- `count_equivalent`: a separately calibrated linear, zero-offset readout in
  detected-photon-equivalent units; negative electronic-noise excursions allowed.
- `arbitrary`: uncalibrated readout (for example volts/ADC units); descriptive
  statistics, temporal changes, and known-ceiling checks only. No conversion to
  counts, Poisson variance comparison, or efficiency conclusion is invented.

`time_s`, when present, must be finite and strictly increasing with spacing
equal to declared bin duration (relative tolerance `1e-6`, absolute tolerance
`dt*1e-9`). A negative initial time is allowed. Analysis uses elapsed bin time;
the absolute time origin is not retained. No resampling or gap filling occurs.
The original file remains unchanged.

Blank data rows, missing/extra fields, nonnumeric/non-finite values, fractional
photon counts, and malformed CSV are rejected. Limits are 32 MiB and 1,000,000
samples per capture; oversized files are rejected, never silently truncated.
Count text is checked before floating-point conversion; counts above `2**53`
are rejected to avoid losing integer precision in the analysis representation.
All rows are validated before any analysis is returned. Recorded captures use
the exact same `analyze(Measurement)` function as simulated observations.

`examples/data/synthetic_counts.csv` is synthetic Poisson data (seed 29,
mean 10, 512 bins). It is an import example, not laboratory validation.
