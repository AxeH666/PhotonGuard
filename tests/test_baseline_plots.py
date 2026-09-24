from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from examples.baseline_plots import counts_figure, distribution_figure


def test_time_plot_uses_bin_centres_and_labels_excerpt():
    counts = np.arange(250, dtype=int)
    figure = counts_figure(counts, 0.001, 10, "Test parameters")
    axes = figure.axes[0]
    np.testing.assert_allclose(axes.lines[0].get_xdata(), (np.arange(200) + 0.5) * 0.001)
    np.testing.assert_array_equal(axes.lines[0].get_ydata(), counts[:200])
    np.testing.assert_array_equal(axes.lines[1].get_ydata(), [10, 10])
    assert "first 200 bins" in axes.get_title()
    assert "(s)" in axes.get_xlabel()
    assert "count" in axes.get_ylabel()


@pytest.mark.parametrize("mean,counts", [(1, np.array([0, 0, 1, 2])), (0, np.zeros(4, dtype=int))])
def test_distribution_mass_and_theory(mean, counts):
    axes = distribution_figure(counts, mean, "Test parameters").axes[0]
    heights = np.array([bar.get_height() for bar in axes.patches])
    assert heights.sum() == pytest.approx(1)
    assert heights[0] == pytest.approx(np.mean(counts == 0))
    assert axes.patches[0].get_x() == -0.5
    theory = axes.lines[0].get_ydata()
    assert theory[0] == pytest.approx(np.exp(-mean))
    assert theory[1] == pytest.approx(mean * np.exp(-mean))
    if mean > 0:
        assert theory[2] == pytest.approx(mean**2 * np.exp(-mean) / 2)
    assert axes.get_ylabel() == "Probability mass"


def test_example_exports_two_pngs_without_gui(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "examples" / "baseline_plots.py"),
         "--output-dir", str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert "Sample mean:" in result.stdout
    assert {path.name for path in tmp_path.iterdir()} == {
        "counts_vs_time.png", "photon_count_distribution.png"
    }
    for path in tmp_path.iterdir():
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert path.stat().st_size > 1000
