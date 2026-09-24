"""Extension example only. It neither connects to hardware nor fabricates data."""

from photonguard.measurement import Measurement


class FutureDeviceSource:
    def read(self) -> Measurement:
        # Future implementation: obtain one finite uniformly timed capture,
        # validate units/calibration and completeness, then construct Measurement.
        # Use a bounded device timeout and release resources even on failure.
        raise NotImplementedError("No device protocol or live hardware driver is implemented")
