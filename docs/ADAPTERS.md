# Source adapter contract (V1)

`MeasurementSource` is a structural Python protocol with one method:

```python
def read(self) -> Measurement:
    ...
```

`SimulationSource` and `CsvSource` implement it. The desktop worker calls
`source.read()`, then the same `analyze(measurement)` function. The diagnostic
engine imports neither source adapters nor the GUI. The pure core needs NumPy;
Qt is not needed to implement or use an adapter.

## One complete capture

Each call returns one finite, nonempty, one-dimensional set of uniformly spaced
observations. V1 does not implement continuous streaming, buffering across reads,
transport discovery, reconnection, or device control. Sources raise on failure;
they must not substitute zeroes, repeat old captures, silently discard gaps, or
return a partial capture as complete. Source-specific I/O errors propagate to the
desktop error panel. The desktop invokes one read at a time in a worker thread.
Future hardware reads must use bounded timeouts and release their resources.

The `Measurement` constructor validates and copies the values into a read-only
float array. It rejects complex/string/boolean arrays, non-finite values, empty
or multidimensional captures, and invalid numeric metadata. Count values must be
nonnegative integers no larger than `2**53`, to preserve exact integer values in
the shared floating-point representation. Durations and optional metadata must
be real numbers, not booleans or strings. Total elapsed duration must be finite.
Arrays and sources are not a thread-safe mutable device API.

Required fields:

| Field | Meaning |
| --- | --- |
| `values` | Observed detector output, **not** hidden incident counts or fault labels |
| `bin_duration_s` | Positive integration/sample interval in seconds; elapsed origin is zero |
| `unit` | `counts`, `count_equivalent`, or `arbitrary` |

Optional fields remain `None` unless justified:

| Field | Meaning |
| --- | --- |
| `expected_mean` | Independent healthy reference mean, in the declared value units |
| `baseline_noise_std` | Healthy electronic noise standard deviation in those units |
| `saturation_level` | Known positive hard readout ceiling in those units |

`counts` means integer photon events. `count_equivalent` assumes normalized
unit-gain, zero-offset photon-equivalent readout, permitting fractional and
negative read noise. `arbitrary` preserves electrical/ADC values without assuming
a count calibration. A device adapter must document any offset/gain conversion,
integration timing and calibration provenance. Do not label volts as counts.
No physical calibration is performed by this interface. Supplied assumptions
remain distinct from observations and diagnostic hypotheses.

`SimulationSource.read()` starts a new generator with its configured seed on
every call; identical parameters repeat the capture. Its expected mean uses the
initial source/efficiency settings, and its baseline electronic noise is zero.
Those are simulator assumptions. `CsvSource.read()` rereads the current file;
caller metadata only supplements matching/missing file context, as in [CSV.md](CSV.md).

## Future device example

[The example stub](../examples/hardware_adapter_stub.py) intentionally raises
`NotImplementedError`. It is not a driver. A future Serial/COM, USB, DAQ,
oscilloscope, TCP/IP or vendor-SDK implementation should acquire a complete
capture, validate timing/units and construct `Measurement`. No subclass registry,
factory, transport package, or diagnostic rewrite is needed. Irregular timestamps
and dropped samples are unsupported; resolve them explicitly upstream rather
than silently resampling. Preserve original laboratory captures separately.

Contract tests compare identical simulation/CSV observations through the engine,
check buffer ownership and seeded reads, reject lossy metadata/values, and ensure
the hardware stub cannot pretend to supply measurements. No hardware compatibility
or live integration has been validated.
