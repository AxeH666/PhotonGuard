import numpy as np
import pytest

from examples.hardware_adapter_stub import FutureDeviceSource
from photonguard.diagnostics import analyze
from photonguard.measurement import Measurement
from photonguard.sources import CsvSource, MeasurementSource, SimulationSource


def test_simulation_and_csv_have_the_same_analysis_contract(tmp_path):
    simulated = SimulationSource(seed=31).read()
    file = tmp_path / "capture.csv"
    with file.open("w") as stream:
        stream.write("# unit=count_equivalent\n# bin_duration_s=0.001\n"
                     "# expected_mean=10\n# baseline_noise_std=0\nvalue\n")
        np.savetxt(stream, simulated.values, fmt="%.17g")
    sources: list[MeasurementSource] = [SimulationSource(seed=31), CsvSource(file)]
    first, second = [source.read() for source in sources]
    np.testing.assert_array_equal(first.values, second.values)
    assert analyze(first) == analyze(second)


def test_seeded_reads_repeat_and_own_their_buffers():
    source = SimulationSource()
    first, second = source.read(), source.read()
    np.testing.assert_array_equal(first.values, second.values)
    assert not np.shares_memory(first.values, second.values)
    assert not first.values.flags.writeable


def test_failed_read_does_not_return_partial_or_fabricated_data(tmp_path):
    with pytest.raises(FileNotFoundError):
        CsvSource(tmp_path / "missing.csv").read()
    with pytest.raises(ValueError):
        SimulationSource(efficiency_end=2).read()
    with pytest.raises(NotImplementedError, match="No device protocol"):
        FutureDeviceSource().read()


@pytest.mark.parametrize("values", [[True], ["1"], [1+2j], [2**53+1]])
def test_adapter_boundary_rejects_silent_lossy_count_coercion(values):
    with pytest.raises(ValueError):
        Measurement(values, 1, "counts")


@pytest.mark.parametrize("metadata", [dict(bin_duration_s=True), dict(bin_duration_s="1"),
    dict(expected_mean=True), dict(baseline_noise_std="0"), dict(saturation_level=1+2j),
    dict(bin_duration_s=1e308)])
def test_adapter_boundary_rejects_invalid_metadata(metadata):
    with pytest.raises(ValueError):
        Measurement([1, 2, 3], unit="counts", **(dict(bin_duration_s=1) | metadata))
