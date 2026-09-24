# PhotonGuard

## Project reference

Read [PhotonGuard Project Scope v1.1](PhotonGuard_Project_Scope_v1.1.docx) before making scope or architecture decisions. This file turns that reference and the founder's instructions into working guidance; it does not authorize implementing the entire roadmap at once.

Follow explicit user instructions for the current task. If the reference and this guidance conflict in a way that affects implementation, explain the conflict before expanding scope.

## Product goal

PhotonGuard is an open-source, Windows-first desktop tool for simulating and diagnosing photon-based QRNG detector measurements.

Build the smallest technically correct tool that:

1. Simulates photon-count measurements and a basic photodetector.
2. Models the four supported detector/measurement failure conditions.
3. Detects deviations from expected physical behaviour.
4. Explains the evidence behind each diagnostic hypothesis.
5. Accepts both simulated data and recorded CSV detector data through the same diagnostics pipeline.
6. Keeps the input boundary suitable for future real hardware adapters.

## V1 scope

Supported fault conditions:

- Detector saturation / clipping.
- Increased electronic noise.
- Source-intensity drift.
- Detector-efficiency degradation.

Also support a healthy baseline for comparison. Provide clear desktop plots, source selection, simulation controls, and diagnostic evidence.

Use Python, NumPy / SciPy as needed, PySide6 / Qt for the desktop UI, and pytest. Development and validation are Windows-first.

## Engineering principles

- Prefer the smallest correct implementation. Do not add infrastructure for hypothetical future requirements.
- Keep the physics model separate from diagnostics and UI.
- Keep data-source adapters separate from analysis. Simulated and recorded data must use the same diagnostic engine.
- Define only the shared measurement representation and metadata needed by implemented features. Document the adapter contract and provide a minimal example stub when that roadmap step is requested.
- Do not couple diagnostics to simulator internals or injected fault labels. Labels may be used as test ground truth, not diagnostic evidence.
- Keep dependencies, configuration, and abstractions proportionate to the current change.

## Physics and diagnostic correctness

- For physics-related changes, state the physical model, assumptions, equations, units, and limitations before implementing when they are not already established.
- Start with the documented photon source, Poisson photon-counting process, and ideal detector baseline. State the conditions under which each model is applicable.
- Distinguish photon counts from electrical measurements. Do not apply count-based relationships to arbitrary recorded values without the required interpretation or calibration.
- Use interpretable metrics where applicable, including mean, variance, clipping rate, bias, autocorrelation, and basic entropy/randomness indicators. Define what each metric measures and when it is meaningful.
- Document diagnostic thresholds and the expected behaviour they compare against. Account for sample size and statistical variability when interpreting evidence.
- Report likely conditions and supporting evidence, never proof of a physical hardware fault.
- When available measurements cannot distinguish competing explanations, report the ambiguity or insufficient evidence rather than force a fault label. State any missing baseline, source reference, or calibration needed for a stronger conclusion.
- Do not equate random-looking output or basic entropy indicators with certified quantum entropy, cryptographic security, or production QRNG validation.
- Diagnostics must be interpretable; do not use a black-box ML classifier in V1.

## Data inputs and adapter boundary

- Fully support simulation and recorded CSV input in V1.
- Validate recorded data and required metadata before analysis. Give clear errors for malformed or unsupported input; do not silently invent missing calibration, units, timing, or detector limits.
- Document the supported CSV format, metadata requirements, and which analyses are unavailable when required context is missing.
- Preserve the distinction between supplied metadata, measured values, and assumptions.
- Keep the adapter boundary suitable for future Serial/COM, USB, DAQ, oscilloscope, TCP/IP, or vendor SDK inputs without building those integrations now.
- Do not claim live-device support or hardware compatibility that has not been implemented and tested.

## Out of scope for V1

Do not implement unless explicitly requested:

- QKD or BB84.
- Post-quantum cryptography.
- AES or encryption demonstrations.
- Quantum computing or Qiskit.
- Vacuum-fluctuation or homodyne QRNG.
- Radioactive-decay simulation.
- Machine-learning fault classification.
- Cloud services or databases.
- Authentication or accounts.
- Web or mobile applications.
- Custom quantum hardware.
- Device-specific live hardware drivers.

Do not claim laboratory-grade calibration, certification, or production-grade QRNG validation.

## Workflow

- Work one focused change at a time. Do not treat the roadmap as authorization to implement later steps.
- For non-trivial, ambiguous, multi-file, or risky work, use a short plan with exactly one step in progress.
- Inspect existing code, configuration, tests, and documentation before making assumptions.
- Diagnose broadly enough to find the real cause, then make the smallest safe change. Avoid unrelated refactors, dependencies, automation, and cleanup.
- Before adding a feature, check whether it directly improves photon-detector simulation, fault diagnosis, recorded-data compatibility, or understanding of the underlying physics. Defer unrelated work.
- Verify current authoritative sources for important physics, architecture, security, or tooling decisions. Distinguish established facts from assumptions and unresolved questions.
- Update directly affected tests and documentation when behaviour changes.
- Run relevant local tests and fix failures caused by the requested change. Use proportionate validation for documentation-only changes.
- Preserve unrelated work, recorded data, and existing evidence. Never expose secrets or credentials.
- Obtain permission before destructive actions, external side effects, or changes beyond the authorized scope. A release roadmap is not permission to publish.
- If the user says stop or hold, stop forward work. If asked to undo, revert only changes made for the current task.
- At handoff, briefly state what changed, what was actually validated, and what remains. Do not claim tests passed or work is complete without verification.

## Locked Git workflow

- One component = one branch = one focused PR.
- Finish and validate the current component before moving on.
- Commit and push the current component branch.
- Open and merge its PR.
- Switch back to `main`.
- Pull the merged remote `main`.
- Only then create the next component branch and begin the next component.
- Never start PR2 work on the PR1 branch.
- Do not bypass this gate unless the founder explicitly changes the workflow.

## Permanent two-stage review rule

- Before every push, perform a self-review of the current component.
- Inspect the actual diff for correctness, scope compliance, unnecessary complexity / overengineering, test adequacy, documentation accuracy, accidental later-roadmap work, and files that should not be included.
- Fix meaningful issues found during self-review before pushing.
- Re-run the relevant tests after any fixes.
- After the branch is pushed and the PR is open, perform a separate independent PR review before merge.
- Treat self-review and independent review as two distinct gates.
- Do not merge or start the next component until the independent review is clean or explicitly approved by the founder.
- These review gates supplement the locked one-component / one-branch / one-focused-PR workflow above; they do not replace it.

## Reference implementation sequence

Follow the v1.1 sequence unless the founder explicitly changes priorities:

1. **Physical baseline:** photon source, Poisson counting, ideal detector, baseline plots, equations, and assumptions.
2. **Detector imperfections:** efficiency, electronic noise, saturation/clipping, source drift, and efficiency degradation.
3. **Diagnostics:** interpretable metrics, expected-versus-observed comparisons, fault rules, evidence, and tests.
4. **Recorded-data interface:** CSV ingestion, validation, metadata, and the shared diagnostic pipeline.
5. **Windows desktop application:** PySide6 / Qt interface, interactive plots, source selection, fault controls, and evidence-first diagnostics.
6. **Hardware-ready input boundary:** stabilize and document the adapter interface and an example stub; no device-specific drivers.
7. **Release polish:** README, physics notes, reproducible examples, tests, screenshots, open-source licensing, and a packaged Windows executable where practical.

Maintain source independence from the start; step 6 formalizes the extension contract rather than introducing a second analysis path.

## V1 acceptance criteria

- Every implemented physical relationship has a documented equation, assumptions, units, and limitations.
- Healthy simulations have reproducible checks across documented normal parameter ranges, with statistical variability considered when evaluating false alarms.
- Each target fault has a reproducible scenario, a useful diagnostic test, and visible supporting evidence. Use explicit random seeds for reproducible simulated examples and tests.
- Fault hypotheses remain qualified, including ambiguous or insufficient-evidence outcomes where appropriate.
- CSV and simulated measurements pass through the same diagnostic engine.
- Major models, plots, and thresholds are explained clearly enough for the owner to understand and defend them.
- The README distinguishes simulated results from claims requiring real laboratory validation and documents the future adapter contract without implying unsupported hardware compatibility.

These are acceptance targets, not claims about the current implementation.
