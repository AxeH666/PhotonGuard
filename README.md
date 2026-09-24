# PhotonGuard

The PR1 physical baseline provides constant-rate photon illumination,
Poisson counts in equal time bins, and an ideal detector. It includes a seeded
example that exports two static PNG plots and focused tests.

PR2 adds binomial detection efficiency, additive electronic read noise, upper
clipping, and controlled source/efficiency profiles in `detector.py`.
See [the physical model and limitations](docs/PHYSICS.md). PR3 adds source-independent
measurements and [interpretable diagnostics](docs/DIAGNOSTICS.md), including
ambiguous and insufficient-evidence outcomes. CSV ingestion, GUI, and hardware
adapters remain later components.
See [the V1 scope](PhotonGuard_Project_Scope_v1.1.docx) and [working guidance](AGENTS.md).

## Physical model

Consider steady coherent light incident on the detector's active area. The source
is described by its expected incident photon rate `r`, in photons per second.
This is a rate at the detector, not the total emission rate of a source with
unspecified optical losses. No propagation, wavelength, or power conversion is
needed for this baseline.

For `M` contiguous, non-overlapping bins, each of duration `dt` seconds:

- Expected count in each bin: `mu = r * dt`.
- Independent incident counts: `N_i ~ Poisson(mu)`.
- Probability of `k` photons: `P(N_i = k) = exp(-mu) * mu**k / k!`.
- Ideal detector: `D_i = N_i`, with no second random draw.
- Expected mean: `E[D_i] = mu`.
- Variance: `Var(D_i) = mu`; standard deviation: `sqrt(mu)`.
- At zero rate, all counts are exactly zero.

Counts are dimensionless event numbers. Plot labels use counts; variance is
expressed as counts squared. Mean and variance are numerically equal under this
model. A steady expected rate does not imply identical counts in every bin.

The example uses `r = 10,000 photons/s`, `dt = 0.001 s`, and `M = 100,000`:
`mu = 10` photons per bin, standard deviation approximately `3.162` counts,
and a total observation time of `100 s`.

### Assumptions and applicability

- Constant expected rate and independent counts in disjoint, equal-duration bins.
- Coherent-state illumination for which Poisson counting is appropriate; not a
  claim that every laser or light source obeys this model.
- An ideal photon counter with 100% efficiency and unlimited counting capacity.
- No dark counts, dead time, missed photons, timing errors, electronic noise,
  gain, or saturation. These effects are absent, not configurable.
- Output is an integer count, not current, voltage, an ADC sample, or a single
  binary click per bin. Several photons may be recorded in one bin.

Directly sampling bin counts is sufficient; individual arrival timestamps and
optical fields are not simulated. Thermal bunching, antibunching, and other
non-Poisson illumination are outside this baseline. Software pseudorandom
sampling reproduces a chosen statistical model, not physical quantum entropy.
These tests establish neither real-detector validity nor cryptographic security.

## Windows setup and use

Run in PowerShell from the project directory. Python 3.10 or newer is required.
Using the virtual environment's executable directly avoids activation-policy
changes and keeps dependencies out of the global Python environment.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[plots,test]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples\baseline_plots.py --output-dir outputs
```

Select another installed supported Python version if 3.12 is unavailable.
The core depends only on NumPy. Matplotlib is the optional plotting dependency;
pytest is the test dependency. The full test suite requires both extras.
There is no SciPy or Qt dependency.

The suite also supports direct invocation: `.\.venv\Scripts\pytest.exe -q`.
Pytest adds the repository root to its import path through `pyproject.toml`, so
both invocation styles can import the example plotting helpers.

The example uses seed `20260924` and the non-interactive Agg backend. It writes:

- `outputs/counts_vs_time.png`: the first 200 bins (0.2 seconds), plotted at bin
  centres, with the theoretical mean. Lines only connect displayed samples;
  they are not a continuous detector waveform.
- `outputs/photon_count_distribution.png`: probability mass from all 100,000
  bins, with integer-centred histogram bins and the theoretical Poisson PMF.

Both figures show the rate, bin duration, total bin count, and seed. The
distribution range includes all observed counts and at least eight standard
deviations above the mean. The theoretical tail is not renormalized. The script
also prints the observed mean and unbiased sample variance. Re-running it replaces
those two PNGs in the selected output directory. Generated outputs are ignored
by Git.

## Small code boundary

- `src/photonguard/baseline.py`: source-count sampling and ideal detection only.
- `examples/baseline_plots.py`: the fixed, reproducible example and plot rendering.
- `tests/`: exact contracts, seeded statistical checks, and plot/export checks.

`sample_photon_counts(rate_per_second, bin_duration_s, n_bins, rng)` returns a
one-dimensional integer NumPy array. Supply a `numpy.random.Generator`; sampling
advances that generator and does not use NumPy's global random state.

Rate must be finite and non-negative; duration finite and positive; bin count a
positive integer. Boolean and string inputs are rejected. An overflowing or
underflowing derived mean is rejected, and NumPy rejects means too close to its
integer output limit. No clipping or silent conversion to zero is used. Array
sizes remain subject to available memory; this is a small in-memory simulator.

`ideal_detect(incident_counts)` accepts a one-dimensional, non-negative integer
array, including an empty integer array, and returns an independent copy. It
does not round fractional measurements or alter counts. No adapter framework or
general measurement schema is introduced in PR 1.

## Validation

Exact tests cover invalid inputs and numeric ranges, array shape/type, zero
illumination, rate-duration conversion, seed repeatability, generator advancement,
preservation of global random state, and ideal-detector count preservation.

Statistical tests use 100,000 bins at each expected mean `0.1, 1, 10, 100`, with
seed `20260924`. For independent Poisson counts and unbiased sample variance
`S^2` (denominator `M - 1`), the sampling standard errors are:

```text
SE(sample mean) = sqrt(mu / M)
SE(S^2)         = sqrt(mu / M + 2 * mu**2 / (M - 1))
```

The variance expression follows from
`Var(S^2) = (central_moment_4 - (M-3)/(M-1) * variance**2) / M`
and the Poisson fourth central moment `mu + 3 * mu**2`.
Both estimates must lie within six standard errors of `mu`. These are
conservative regression tolerances, not certified confidence levels or diagnostic
thresholds. The zero-rate case is tested exactly rather than divided by a zero
standard error. A single additional sanity check tests `P(N=0) = exp(-1)` at
`mu = 1` against six binomial standard errors, using seed `123`.

Plot checks verify bin-centre times, the displayed excerpt and expected mean,
histogram normalization, selected theoretical probabilities, axis labels, and
PNG export without a GUI. Human inspection checks readability of generated plots.
Matching these moments and one probability does not prove the complete joint
distribution or independence; the implementation relies on NumPy's established
Poisson sampler rather than introducing a new random-number algorithm.

Repeatability is scoped to the same seed, generator, calls, and NumPy environment.
Exact streams are not promised across arbitrary dependency versions or machines.

### Verified local result

On Windows, September 24, 2026, the full suite passed: **50 tests in 6.46 s**.
The environment used Python 3.12.10, NumPy 2.5.2, Matplotlib 3.11.1, and
pytest 9.1.1. Dependencies were installed into `.venv` from the local uv cache;
`python -m pip check` reported no broken requirements. Other supported Python
versions have not been tested in this change.

The documented example produced both PNGs. Its sample mean was `10.003240`
and unbiased variance was `10.091070`, compared with theoretical values of `10`.
Both were within the documented sampling-error bounds. Both 1350-by-720 images
were visually inspected for readable labels, legends, model overlays, and absence
of clipping. Generated images remain in `outputs/` locally.

To select the same direct dependency versions when reproducing this run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[plots,test]" "numpy==2.5.2" "matplotlib==3.11.1" "pytest==9.1.1"
```

## References

- [MIT 6.453, Lecture 19](https://ocw.mit.edu/courses/6-453-quantum-optical-communication-fall-2016/f9cfc500b287e4531f4255f7e5adbfcd_MIT6_453F16_Lect19_Notes.pdf),
  pages 1-2: coherent-state illumination and Poisson photocount processes.
- [MIT 22.51 notes](https://live.ocw.mit.edu/courses/22-51-quantum-theory-of-radiation-interactions-fall-2012/693972cea9cf9da5e4e9e86fbc72c9e7_MIT22_51F12_Notes.pdf),
  section 10.4: coherent-state photon statistics and shot-noise scaling.
- [NumPy Poisson sampler](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html)
  and [random-stream compatibility](https://numpy.org/doc/stable/reference/random/compatibility.html).
- [Matplotlib non-interactive plotting](https://matplotlib.org/stable/gallery/user_interfaces/canvasagg.html).
