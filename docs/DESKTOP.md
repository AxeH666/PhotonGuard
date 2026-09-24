# Windows desktop use

Install `.[gui,test]` in the project virtual environment, then launch
`python -m photonguard` or the installed `photonguard` command. Qt Widgets comes
from PySide6-Essentials; unused Qt add-on modules are not required. See the
[official package split](https://doc.qt.io/qtforpython-6/package_details.html).
The plots use Matplotlib's [Qt canvas and toolbar](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html).

Choose **Simulation** or **Recorded CSV**, then **Capture and analyze**. Results
describe the completed capture, not subsequent edits to the controls. Capturing
again clears the old results first. Failures display an error without retaining
a previous diagnosis. File reading and analysis run in a worker thread. Closing
during a capture is deferred: close again after the capture finishes.

## Simulation

The start/end incident rates (photons/s) and efficiencies (dimensionless, 0–1)
define linear profiles between bin centres. Noise standard deviation and the
optional upper clipping limit use detected-photon-equivalent readout units.
The documented [physical model](PHYSICS.md) applies without changes.

Presets reset controls to 10,000 bins, 1 ms/bin, seed 29, initial incident rate
10,000 photons/s and efficiency 1. Healthy uses constant rate/efficiency and no
noise or clipping. Clipping sets the upper limit to 8; noise sets its standard
deviation to 4; source drift halves the final rate; efficiency degradation halves
the final efficiency. Controls remain editable. The scenario name is never
diagnostic evidence. Source dimming and efficiency loss can produce the same
distribution; their diagnoses deliberately remain ambiguous.

Simulation declares its initial expected detected mean as the reference and
zero read noise as the healthy reference. These are explicit model assumptions,
not measurements or laboratory calibration. Captures use 1–100,000 bins; the
diagnostic minimum is 256. The seed provides software repeatability within the
same dependency environment, not physical quantum randomness.

## Recorded CSV

Browse for a [supported CSV](CSV.md). Metadata can come from the file or the
optional input fields. Leave fields blank to use file metadata. Matching metadata
is allowed; conflicts are errors. Missing context is not inferred from the data.
An arbitrary-unit voltage/ADC capture can be plotted and checked for temporal
change or a supplied ceiling, but is not automatically interpreted as counts.

## Results

The time plot displays the first 2,000 bins at their elapsed bin-centre times;
the histogram and diagnostics use **all** bins. The title makes the excerpt
explicit. Lines between samples are visual connectors, not a continuous waveform.
The histogram shows probability per displayed interval, not probability density
or a fitted Poisson distribution. The dashed line is the supplied reference mean.
Use the plot toolbar to pan, zoom, reset, or save the displayed figure.
If a numeric range cannot be rendered, the evidence remains available and the
panel reports the plotting limitation.

The evidence panel lists observed findings, competing explanations, declared
metadata, [metrics and limitations](DIAGNOSTICS.md). Variance uses squared value
units; mean and early/late change use value units; fractions and correlations
are dimensionless; threshold-bit entropy is in bits. It is not a quantum entropy
estimate. No-anomaly results apply only to available checks and do not certify
hardware health, security, calibration, or a production QRNG.

Automated GUI tests default to Qt's offscreen platform so they do not require
an interactive desktop. Native Windows launch/render checks are separate; the
application itself uses the normal Windows platform, not the test override.
