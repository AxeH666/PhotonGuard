import numpy as np
import pytest

from photonguard.csv_input import load_csv
from photonguard.diagnostics import analyze
from photonguard.measurement import Measurement


def write_capture(tmp_path, text):
    path = tmp_path / "capture.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_csv_and_simulated_observations_use_identical_diagnostics(tmp_path):
    values = np.random.default_rng(29).poisson(10, 2048)
    data = Measurement(values, 0.001, "counts", 10, 0)
    path = write_capture(tmp_path, "# Synthetic test data\n# unit=counts\n# bin_duration_s=0.001\n"
        "# expected_mean=10\n# baseline_noise_std=0\nvalue,time_s\n" +
        "\n".join(f"{v},{i * 0.001:.9f}" for i, v in enumerate(values)))
    original = path.read_bytes()
    imported = load_csv(path)
    np.testing.assert_array_equal(imported.values, data.values)
    assert analyze(imported) == analyze(data)
    assert path.read_bytes() == original


def test_missing_metadata_can_be_supplied_without_inventing_baseline(tmp_path):
    path = write_capture(tmp_path, "value\n1.2\n-0.3\n")
    data = load_csv(path, metadata={"unit": "arbitrary", "bin_duration_s": 0.01})
    assert data.expected_mean is None and data.baseline_noise_std is None
    assert analyze(data).status == "insufficient_evidence"


@pytest.mark.parametrize("text", [
    "value\n1\n", "# unit=counts\n# bin_duration_s=1\nvalue\n",
    "# unit=counts\n# unit=counts\n# bin_duration_s=1\nvalue\n1\n",
    "# fault=healthy\n# unit=counts\n# bin_duration_s=1\nvalue\n1\n",
    "# unit=counts\n# bin_duration_s=bad\nvalue\n1\n",
    "# unit=counts\n# bin_duration_s=1\nother\n1\n",
])
def test_invalid_schema_or_metadata(tmp_path, text):
    with pytest.raises(ValueError):
        load_csv(write_capture(tmp_path, text))


@pytest.mark.parametrize("rows", ["nan", "inf", "1.5", "-1", "=1+1", "1,2", "", '"1', "1\n\n2",
    "1.00000000000000000001", "9007199254740993"])
def test_invalid_values_are_not_dropped_or_repaired(tmp_path, rows):
    path = write_capture(tmp_path, "# unit=counts\n# bin_duration_s=1\nvalue\n" + rows)
    with pytest.raises(ValueError):
        load_csv(path)


@pytest.mark.parametrize("times", ["0\n2", "1\n0", "0\n0", "0\nnan"])
def test_irregular_timing_rejected(tmp_path, times):
    first, last = times.splitlines()
    path = write_capture(tmp_path, f"# unit=counts\n# bin_duration_s=1\nvalue,time_s\n1,{first}\n2,{last}")
    with pytest.raises(ValueError, match="time_s"):
        load_csv(path)


def test_conflicting_metadata_rejected(tmp_path):
    path = write_capture(tmp_path, "# unit=counts\n# bin_duration_s=1\nvalue\n1")
    with pytest.raises(ValueError, match="Conflicting"):
        load_csv(path, metadata={"unit": "arbitrary"})


def test_utf8_bom_and_time_first_column(tmp_path):
    path = write_capture(tmp_path, "\ufeff# unit=counts\n# bin_duration_s=0.5\ntime_s,value\n-1,3\n-0.5,4")
    np.testing.assert_array_equal(load_csv(path).values, [3, 4])


def test_sample_limit_rejects_entire_capture(tmp_path, monkeypatch):
    monkeypatch.setattr("photonguard.csv_input.MAX_SAMPLES", 2)
    path = write_capture(tmp_path, "# unit=counts\n# bin_duration_s=1\nvalue\n1\n2\n3")
    with pytest.raises(ValueError, match="sample limit"):
        load_csv(path)
