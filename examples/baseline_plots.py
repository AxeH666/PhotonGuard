"""Generate two static PNGs for the documented, seeded baseline example."""

import argparse
from math import exp, lgamma, log
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure
import numpy as np

from photonguard.baseline import ideal_detect, sample_photon_counts


def counts_figure(counts, bin_duration_s, expected_mean, caption):
    """Plot the first 200 bins of validated baseline counts, at bin centres."""
    shown = counts[:200]
    time_s = (np.arange(shown.size) + 0.5) * bin_duration_s
    figure = Figure(figsize=(9, 4.8), layout="constrained")
    axes = figure.subplots()
    axes.plot(time_s, shown, color="#2563a6", marker=".", linewidth=0.8,
              label="Simulated counts")
    axes.axhline(expected_mean, color="#c45120", linestyle="--",
                 label=f"Expected mean = {expected_mean:g}")
    axes.set(title=f"Ideal photon counts | first {shown.size} bins",
             xlabel="Time at bin centre (s)", ylabel="Photons detected per bin (count)")
    axes.set_ylim(bottom=0)
    axes.grid(alpha=0.2)
    axes.legend(loc="upper right")
    figure.suptitle(caption, fontsize=10)
    return figure


def distribution_figure(counts, expected_mean, caption):
    """Plot empirical mass and the Poisson PMF for the small baseline example.

    The displayed range covers all observed counts and at least eight standard
    deviations above the mean. The theoretical tail is not renormalized.
    """
    upper = max(int(counts.max()),
                int(np.ceil(expected_mean + 8 * np.sqrt(expected_mean))), 1)
    k = np.arange(upper + 1)
    if expected_mean == 0:
        probabilities = np.zeros(k.size)
        probabilities[0] = 1
    else:
        # Log form avoids factorial overflow, without a SciPy dependency.
        probabilities = np.array([
            exp(int(value) * log(expected_mean) - expected_mean - lgamma(int(value) + 1))
            for value in k
        ])

    figure = Figure(figsize=(9, 4.8), layout="constrained")
    axes = figure.subplots()
    axes.hist(counts, bins=np.arange(-0.5, upper + 1.5),
              weights=np.full(counts.size, 1.0 / counts.size),
              color="#2563a6", alpha=0.65, label="Simulated probability mass")
    axes.plot(k, probabilities, color="#c45120", marker="o", markersize=3,
              linewidth=1.2, label=f"Poisson model (mean = {expected_mean:g})")
    axes.set(title=f"Photon-count distribution | all {counts.size:,} bins",
             xlabel="Photons detected per bin (count)", ylabel="Probability mass")
    axes.grid(axis="y", alpha=0.2)
    axes.legend()
    figure.suptitle(caption, fontsize=10)
    return figure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    rate_per_second = 10_000.0
    bin_duration_s = 0.001
    n_bins = 100_000
    seed = 20260924
    mean_count = rate_per_second * bin_duration_s
    counts = ideal_detect(sample_photon_counts(
        rate_per_second, bin_duration_s, n_bins, np.random.default_rng(seed)
    ))
    caption = (f"Rate: {rate_per_second:g} photons/s | Bin: {bin_duration_s:g} s"
               f" | Total bins: {n_bins:,} | Seed: {seed}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, figure in (
        ("counts_vs_time.png", counts_figure(counts, bin_duration_s, mean_count, caption)),
        ("photon_count_distribution.png", distribution_figure(counts, mean_count, caption)),
    ):
        path = args.output_dir / filename
        figure.savefig(path, dpi=150)
        print(path.resolve())
    print(f"Expected mean/variance: {mean_count:g}")
    print(f"Sample mean: {counts.mean():.6f}; unbiased variance: {counts.var(ddof=1):.6f}")


if __name__ == "__main__":
    main()
