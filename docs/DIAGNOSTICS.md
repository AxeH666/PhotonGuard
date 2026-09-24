# Diagnostic interpretation

The engine accepts only `Measurement`: observed values, bin duration in seconds,
declared units, and optional expected healthy mean, baseline electronic noise
standard deviation, and readout ceiling. It does not import the simulator or
accept fault labels, hidden efficiency, or injected source profiles.

Metadata is supplied context, not evidence that a device actually has that
calibration. For simulation, a declared baseline is a model assumption. For real
captures it must be justified separately. Unknown values stay unknown.

## Rules

Screening requires 256 bins. Mean and unbiased variance describe the values.
Lag-one correlation checks dependence between adjacent bins; it is undefined for
constant samples. Compare the first and last quarters: `delta = mean_last -
mean_first`, with `SE = sqrt(var_first/q + var_last/q)`. A change must exceed
both six standard errors and 10% of the full-sample absolute mean. This detects
level change, not a proof of a smooth trend or its cause. A rising mean suggests
source-intensity change with efficiency/gain alternatives; a falling mean lists
both source drift and efficiency degradation. No unique localization is possible
from this channel because `E[K] = eta*r*dt`.

For a supplied positive upper limit `L`, samples satisfying
`abs(value - L) <= 1e-9 * abs(L)` are counted as at the ceiling
(`numpy.isclose(value, L, rtol=1e-9, atol=0)`). The same comparison permits tiny
numerical excursions above `L`; values above `L` outside this band invalidate
the metadata and cause abstention. There is no fixed absolute tolerance that
could dominate small electrical values. This preserves the relative comparison
when arbitrary-unit values and their ceiling are rescaled together, subject to
floating-point representability. If the tolerance underflows to zero, only exact
equality qualifies. This numerical band is not an instrument calibration or
resolution estimate; count/count-equivalent units retain their defined scale.

A clipping hypothesis requires over 5% occupancy and, for
integer count ceilings with zero/unknown baseline read noise, more than ordinary
Poisson mass `P(N=L)` plus six binomial standard errors. Supplied baseline mean
is used when present, otherwise the sample mean is only a screening estimate.
This check is for hard clipping; soft compression may be missed. Quantization
and repeated/censored records can imitate clipping. Unknown ceiling means no
clipping check, not a claim that clipping is absent.

In stationary, unclipped, calibrated count/count-equivalent data, expected
variance is `v0 = max(sample_mean,0) + baseline_noise_std**2`. Under independent
Poisson plus Gaussian noise, the variance-estimate standard error is
`sqrt(lambda/n + 2*v0**2/(n-1))`, using `lambda=max(sample_mean,0)` as a plug-in
estimate. Excess must exceed both six standard errors and 20% of `v0` to suggest
electronic-noise increase. Source fluctuations and model mismatch are alternatives.
Too little variance is a model-mismatch warning. Temporal changes suppress this
stationary noise check; clipping suppresses all unclipped mean/variance rules.

Mean departure from a supplied baseline must exceed six standard errors
`sqrt(max(sample_variance,baseline_mean,1e-12)/n)` and 10% of baseline mean.
Absolute lag-one correlation above `max(0.1,6/sqrt(n))` in otherwise stationary
data produces a model-mismatch warning. These cutoffs are deliberately conservative
engineering heuristics with practical effect-size floors, not calibrated
confidence scores, universal sensitivity guarantees, or formal certification.

## Outcomes and descriptive indicators

- `no_anomaly_detected`: no applicable check found an anomaly, with sufficient
  samples and a supplied count-model baseline. Not proof of hardware health.
- `likely_condition`: clipping or excess variance supports a qualified hypothesis.
- `ambiguous`: a mean change or model mismatch has competing explanations.
- `insufficient_evidence`: too few samples, unsuitable/missing context, an invalid
  ceiling, or uninformative all-zero data prevents baseline acceptance.

Arbitrary electrical units retain descriptive summaries and temporal/ceiling
checks; no Poisson noise or efficiency conclusion is made without calibrated
count units. Negative values are valid for zero-offset count-equivalent readout.

The descriptive binary sequence is `b_i = 1[value_i > sample_median]`.
Its bias is `mean(b)-0.5`; binary Shannon entropy is
`-p*log2(p)-(1-p)*log2(1-p)`, with zero terms defined by continuity.
Ties can cause bias even for an ideal Poisson process. These indicators are not
used for fault classification and do not measure physical quantum entropy,
min-entropy, unpredictability, or cryptographic security.

Tests cover healthy seeds, all four scenarios, deliberate ambiguity, missing
metadata, invalid captures, and suppression of misleading noise conclusions.
