# V1.1 acceptance and validation record

Validation uses synthetic data unless explicitly stated otherwise. No laboratory
capture or physical detector was available. The acceptance target is a defensible
diagnostic prototype, not certification or universal fault detection.

## Acceptance mapping

| V1.1 criterion | Implementation and evidence |
| --- | --- |
| Documented physical relationships | `PHYSICS.md`: Poisson incident counts, binomial efficiency, Gaussian read noise, hard clipping, units and omissions; exact/statistical model tests |
| Healthy behaviour under normal ranges | 32 seeded checks: expected detected means 0.1, 1, 10, 100; efficiencies 0.2/0.8; declared noise std 0/2; seeds 7/29; 10,000 bins each; no diagnostic findings in this fixed grid |
| Four reproducible faults with evidence | `examples/scenarios.py`, diagnostic and GUI tests; clipping/noise hypotheses and ambiguous drift/degradation with alternatives |
| No hardware-fault proof claims | Qualified findings, competing explanations, insufficient-evidence states, permanent limits in each report |
| Same simulated/recorded pipeline | `MeasurementSource.read() -> Measurement -> analyze`; exact-value CSV round trips produce identical reports |
| Explainable plots/models/thresholds | `DESKTOP.md`, `PHYSICS.md`, `DIAGNOSTICS.md`; time excerpt explicitly labelled; histogram uses all samples |
| Simulation vs laboratory claims separated | README and reports state pseudorandom/idealized assumptions, no entropy/security/calibration certification |
| Desktop application | Offscreen Qt integration tests plus separate native Windows five-preset/CSV smoke and inspected screenshots |
| Future hardware boundary | `ADAPTERS.md`, contract tests and an explicitly unimplemented example; no live drivers |
| Open-source release material | MIT license, dependency notices, reproducible examples, screenshots and portable Windows build procedure |

## Focused statistical checks

PR1 uses 100,000 bins at Poisson means `0.1, 1, 10, 100`, seed `20260924`.
Mean and unbiased sample variance must agree within six sampling standard errors:

```text
SE(mean) = sqrt(mu / n)
SE(S^2) = sqrt(mu / n + 2*mu**2 / (n-1))
```

The variance expression follows from the Poisson fourth central moment
`mu + 3*mu**2` and `Var(S^2)=[mu4-(n-3)/(n-1)*variance**2]/n`.
Zero-rate and ideal count preservation are exact contracts. A lightweight check
of `P(N=0)=exp(-1)` at mean 1 uses six binomial standard errors. Detector tests
verify exact efficiency endpoints/clipping and seeded thinning/noise moments.

Diagnostic thresholds have their own documented sample-size and effect-size
floors; they are not those regression tolerances. The healthy test grid is finite,
not proof of zero false positives. Multiple comparisons, unknown calibration,
subtle faults and combined faults can defeat screening. No sensitivity/specificity
or confidence-score calibration is claimed. Baseline test success does not prove
the complete joint distribution or physical independence.

The static PR1 example gives mean **10.003240** and unbiased variance
**10.091070**, compared with expected **10**. Its two separate PNGs show the first
200 bins and the full distribution with Poisson PMF; both are visually inspected.
Desktop plots use a first-2,000-bin excerpt and full-capture histogram instead.

## Release environment and results

Windows 11 Home (10.0.26200), x64, Python 3.12.10; NumPy 2.5.2, Matplotlib 3.11.1,
PySide6-Essentials/Shiboken 6.11.2, pytest 9.1.1, PyInstaller 6.22.3.
The exact dependency snapshot is `requirements-windows.txt`.

Pre-merge PR7 release candidate checks on September 24, 2026:

| Check | Actual result |
| --- | --- |
| `python -m pytest -q` | 178 passed in 4.83 s; no skips |
| `pytest -q` | 178 passed in 4.73 s; no skips |
| `python -m pip check` | No broken requirements |
| Native source desktop smoke | All five scenarios plus CSV completed; Qt platform `windows`; screenshots inspected |
| Frozen Windows executable smoke | Exit 0 from outside the checkout, all six statuses and expected hypotheses checked; Qt platform `windows` |
| Baseline plots and scenarios | Both baseline PNGs generated/inspected; five CSVs and reports reproduced and round-trip tests passed |
| PyInstaller | One-directory executable built successfully; QtAgg selected; no build error or warning |

The final local candidate is `dist/v1.1.0/PhotonGuard/PhotonGuard.exe`; its SHA-256
is `870d63c6ada9a5d9d400ce6832ef777b28bed7c8d0b6527df29b29c31c705bbe`.
Keep the complete directory with the executable. PyInstaller's missing-module
report contains optional/cross-platform imports; the exercised runtime paths
passed. This is not proof that every optional third-party code path works.

The executable is generated locally, not tracked in Git or uploaded as a GitHub
release asset. Source, build recipe, screenshots and dependency notices are tracked.

## Remaining boundaries

- The model omits dark counts, dead time, afterpulsing, detector-specific gain,
  soft compression, non-Poisson illumination and non-Gaussian/colored read noise.
- Source intensity, coupling and detector efficiency cannot be uniquely separated
  from a single mean-count channel. Arbitrary units do not imply count calibration.
- Captures are finite and uniformly timed; no live drivers, streaming lifecycle,
  dropped-sample correction or irregular-time resampling is implemented.
- Tests and screenshots are software evidence. Real captures, calibration,
  device compatibility, physical entropy and laboratory performance are unverified.
- No clean-machine/other-Windows-version matrix, installer, signing, or production
  deployment has been validated. See `RELEASE.md` for the native-pytest COM issue.
- Per-PR self-reviews are complete; the founder-deferred independent review of
  the complete implementation is still a separate gate.
