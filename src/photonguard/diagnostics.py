"""Conservative, interpretable measurement checks; no simulator dependency."""

from dataclasses import dataclass
from math import exp, lgamma, log

import numpy as np

from photonguard.measurement import Measurement


@dataclass(frozen=True)
class Finding:
    condition: str
    evidence: str
    alternatives: str


@dataclass(frozen=True)
class Report:
    status: str
    metrics: dict[str, float | None]
    findings: tuple[Finding, ...]
    limitations: tuple[str, ...]


def analyze(measurement: Measurement) -> Report:
    """Analyze supplied observations and declared baseline metadata only.

    Rule thresholds are engineering screening heuristics, not calibrated
    confidence scores. See docs/DIAGNOSTICS.md for equations and applicability.
    """
    x = measurement.values
    n = x.size
    with np.errstate(over="ignore", invalid="ignore"):
        mean = float(x.mean())
        variance = float(x.var(ddof=1)) if n > 1 else 0.0
    if not np.isfinite([mean, variance]).all():
        raise ValueError("Measurement moments overflow; rescale the recorded units")
    p = float(np.mean(x > np.median(x)))
    entropy = float(-p * np.log2(p) - (1 - p) * np.log2(1 - p)) if 0 < p < 1 else 0.0
    correlation = None
    if n > 2 and x[:-1].std() > 0 and x[1:].std() > 0:
        correlation = float(np.corrcoef(x[:-1], x[1:])[0, 1])
    metrics = {"n_bins": float(n), "mean": mean, "variance": variance,
               "lag1_correlation": correlation, "above_median_fraction": p,
               "threshold_bit_bias": p - 0.5, "threshold_bit_entropy": entropy,
               "clipping_fraction": None, "early_late_change": None}
    limits = ["Diagnostic hypotheses are not proof of a physical hardware fault.",
              "Threshold-bit bias and entropy describe this sample only; they do not measure quantum entropy or security."]
    findings = []
    if n < 256:
        limits.append("At least 256 bins are required for screening; collect a longer capture.")
        return Report("insufficient_evidence", metrics, (), tuple(limits))

    count_units = measurement.unit in {"counts", "count_equivalent"}
    mu0 = measurement.expected_mean
    noise0 = measurement.baseline_noise_std
    if not count_units:
        limits.append("Uncalibrated arbitrary units: Poisson variance and efficiency checks are unavailable.")
    if mu0 is None or noise0 is None:
        limits.append("Missing expected mean or baseline noise: absolute baseline agreement cannot be established.")

    ceiling = measurement.saturation_level
    clipped = False
    if ceiling is None:
        limits.append("No known readout ceiling supplied; clipping cannot be reliably screened.")
    elif np.any(x > ceiling + 1e-9 * max(1, ceiling)):
        limits.append("Samples exceed the supplied ceiling; check metadata or units before interpreting clipping.")
        return Report("insufficient_evidence", metrics, (), tuple(limits))
    else:
        fraction = float(np.mean(np.isclose(x, ceiling, rtol=0, atol=1e-9 * max(1, ceiling))))
        metrics["clipping_fraction"] = fraction
        # Account for ordinary probability mass at an integer photon count.
        natural_mass = 0.0
        if fraction > 0 and count_units and ceiling == int(ceiling) and (noise0 is None or noise0 == 0):
            candidate_mean = max(mean, 0) if mu0 is None else mu0
            if candidate_mean > 0:
                natural_mass = exp(ceiling * log(candidate_mean) - candidate_mean - lgamma(ceiling + 1))
        threshold = max(0.05, natural_mass + 6 * np.sqrt(natural_mass * (1 - natural_mass) / n))
        if fraction > threshold:
            clipped = True
            findings.append(Finding("saturation_clipping",
                f"{fraction:.1%} of samples equal the supplied ceiling {ceiling:g}; screening threshold {threshold:.1%}.",
                "A hard limit, quantization, or repeated/censored data can produce this pattern."))

    quarter = n // 4
    first, last = x[:quarter], x[-quarter:]
    change = float(last.mean() - first.mean())
    change_se = float(np.sqrt(first.var(ddof=1) / quarter + last.var(ddof=1) / quarter))
    metrics["early_late_change"] = change
    trend = abs(change) > max(6 * change_se, 0.10 * max(abs(mean), 1e-12))
    if clipped:
        limits.append("Clipping invalidates unclipped moment/efficiency rules; those rules are suppressed.")
    else:
        if trend:
            evidence = f"Last-quarter mean minus first-quarter mean = {change:.4g}; standard error {change_se:.4g}."
            findings.append(Finding("source_intensity_drift", evidence,
                "Source variation, optical coupling, detector efficiency, or readout gain can change the mean."))
            if change < 0 and count_units:
                findings.append(Finding("efficiency_degradation", evidence,
                    "Source dimming and optical loss are indistinguishable without an independent source reference."))
            limits.append("Temporal change suppresses stationary noise rules; a changing mean can itself increase variance.")

        if count_units and not trend:
            lam = max(mean, 0.0)
            if noise0 is not None:
                with np.errstate(over="ignore"):
                    expected_variance = lam + np.float64(noise0)**2
                if not np.isfinite(expected_variance):
                    raise ValueError("Baseline noise variance exceeds supported numeric range")
                variance_se = np.hypot(np.sqrt(lam / n), expected_variance * np.sqrt(2 / (n - 1)))
                tolerance = max(6 * variance_se, 0.20 * expected_variance, 1e-12)
                if variance - expected_variance > tolerance:
                    findings.append(Finding("electronic_noise_increase",
                        f"Variance {variance:.4g} exceeds shot-noise plus baseline read-noise variance {expected_variance:.4g} by more than {tolerance:.4g}.",
                        "Unresolved source fluctuations, colored noise, or model mismatch can also cause excess variance."))
                elif expected_variance - variance > tolerance:
                    findings.append(Finding("model_mismatch",
                        f"Variance {variance:.4g} is below expected {expected_variance:.4g}.",
                        "Smoothing, quantization, unknown clipping, or non-Poisson illumination may be present."))
            if mu0 is not None:
                mean_se = np.sqrt(max(variance, mu0, 1e-12) / n)
                if abs(mean - mu0) > max(6 * mean_se, 0.10 * max(mu0, 1e-12)):
                    evidence = f"Mean {mean:.4g} differs from declared baseline {mu0:.4g}."
                    findings.append(Finding("source_intensity_drift", evidence,
                        "Source level, optical loss, efficiency, or gain may differ from the baseline."))
                    if mean < mu0:
                        findings.append(Finding("efficiency_degradation", evidence,
                            "A lower mean alone cannot distinguish efficiency loss from a dimmer source."))

        if correlation is not None and abs(correlation) > max(0.1, 6 / np.sqrt(n)) and not trend:
            findings.append(Finding("model_mismatch",
                f"Lag-one correlation {correlation:.4g} is inconsistent with the independent-bin assumption at the screening threshold.",
                "Filtering, correlated electronics, or source fluctuations can correlate samples."))

    if findings:
        # Mean changes are intrinsically underdetermined from this channel.
        ambiguous = any(f.condition in {"source_intensity_drift", "efficiency_degradation", "model_mismatch"} for f in findings)
        status = "ambiguous" if ambiguous else "likely_condition"
    elif not count_units or mu0 is None or noise0 is None or (mean == 0 and variance == 0):
        status = "insufficient_evidence"
        if mean == 0 and variance == 0:
            limits.append("All-zero data cannot demonstrate a functioning illuminated detector.")
    else:
        status = "no_anomaly_detected"
        limits.append("No anomaly in applicable checks; this is not a hardware-health certificate.")
    return Report(status, metrics, tuple(findings), tuple(limits))
