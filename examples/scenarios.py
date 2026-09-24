"""Reproduce the five desktop scenarios as explicitly synthetic CSV + reports."""

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np

from photonguard.diagnostics import analyze
from photonguard.sources import SimulationSource


def scenarios():
    baseline = SimulationSource(seed=29)
    return {
        "healthy": baseline,
        "clipping": replace(baseline, ceiling=8),
        "electronic_noise": replace(baseline, noise_std=4),
        "source_drift": replace(baseline, rate_end=5000),
        "efficiency_degradation": replace(baseline, efficiency_end=.5),
    }


def generate(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name, source in scenarios().items():
        measurement = source.read()
        # The name is example ground truth, not an input to analyze().
        report = analyze(measurement)
        reports[name] = asdict(report)
        with (output_dir / f"{name}.csv").open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("# Synthetic PhotonGuard example; pseudorandom seed 29\n")
            for key in ("unit", "bin_duration_s", "expected_mean", "baseline_noise_std", "saturation_level"):
                value = getattr(measurement, key)
                if value is not None:
                    stream.write(f"# {key}={value}\n")
            stream.write("value\n")
            np.savetxt(stream, measurement.values, fmt="%.17g")
    (output_dir / "reports.json").write_text(json.dumps(reports, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/scenarios"))
    args = parser.parse_args()
    for name, report in generate(args.output_dir).items():
        print(f"{name}: {report['status']}")
