# Physical model and limitations

## Physical situation and ideal baseline

The rate is that of steady coherent light incident on the active detector area,
not total source emission before unspecified optical losses. Each equal-duration,
non-overlapping bin counts events, not a single binary click. Poisson probability
is `P(N=k)=exp(-mu)*mu**k/k!`, with `mu=r*dt`. An ideal detector returns `D_i=N_i`
without a second draw; `E[D]=Var(D)=mu` numerically and `std(D)=sqrt(mu)`.
Counts are dimensionless event numbers; plots label them as counts and variance
as counts squared. Zero illumination gives exactly zero ideal counts.

This assumes independent bins and coherent-state illumination for which Poisson
photodetection applies. It is not a statement about every laser. The baseline
does not model fields, arrival times, propagation, wavelength, power conversion,
thermal bunching or antibunching. Specifying incident rate avoids inventing
optical collection efficiency or a wavelength-to-power calibration.

## Incident photons and detection

The PR1 baseline remains unchanged. For each bin of duration `dt` seconds,
`N_i ~ Poisson(r_i * dt)` independently, where `r_i` is incident photons/second
at the active detector area. Constant `r_i` recovers the baseline. A supplied
rate profile is piecewise constant within each bin. `linear_profile` describes
values at first/last bin centres, inclusive; a single bin uses the first value.

Given incident integer count `N_i`, detected integer count
`K_i | N_i ~ Binomial(N_i, eta_i)`, where `eta_i` is a dimensionless independent
detection probability in `[0, 1]`. Consequently `K_i ~ Poisson(eta_i*r_i*dt)`.
For constant rate and efficiency, its mean and variance are both `eta*r*dt`.
We retain incident and detected arrays separately; detection cannot create more
photons than arrived. Efficiency one records all photons; zero records none.

## Electronic readout and clipping

`X_i = K_i + epsilon_i`, with independent `epsilon_i ~ Normal(0, sigma_e**2)`.
`sigma_e` has detected-photon-equivalent count units. This is a normalized linear
readout with assumed unit gain and zero offset, not a current/voltage/ADC model.
Before clipping, `E[X_i] = eta_i*r_i*dt` and
`Var(X_i) = eta_i*r_i*dt + sigma_e**2`. Negative noise excursions are allowed;
rounding or lower clipping would bias this model and is not applied.

Optional upper saturation is `Y_i = min(X_i, L)`, where finite `L > 0` is in the
same units. This models a hard readout ceiling, not detector dead time or a
complete electronics transfer function. Clipping changes the above moments;
unclipped Poisson formulas must not be assumed for the clipped samples.

## Four controlled scenarios

- Saturation: increase incident rate relative to a chosen readout ceiling.
- Electronic noise increase: increase `sigma_e` from a stated baseline.
- Source drift: vary `r_i` linearly over bin centres, holding efficiency fixed.
- Efficiency degradation: decrease `eta_i` linearly, holding incident rate fixed.

Linear profiles are reproducible stress scenarios, not predictions of device
aging. No dark counts, dead time, afterpulsing, crosstalk, gain drift, optical
propagation, or non-Poisson light states are modeled. These omissions limit
interpretation of real data. Gaussian noise is a basic additive electronics
approximation; real read noise can be colored or non-Gaussian.

Mean detected counts depend on the product `eta*r`. A fall in measured output
alone cannot distinguish source dimming, optical loss, and lower efficiency.
Any later diagnostic must retain that ambiguity without a relevant independent
reference. Simulator parameters/labels are not measured evidence of a fault.

## References

- [MIT 6.453 lecture 19, pages 1-2](https://ocw.mit.edu/courses/6-453-quantum-optical-communication-fall-2016/f9cfc500b287e4531f4255f7e5adbfcd_MIT6_453F16_Lect19_Notes.pdf):
  coherent illumination and efficiency-scaled Poisson photodetection.
- [NumPy binomial sampler](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html):
  conditional independent detection trials. Counts are validated as integers
  before calling it; its permissive float truncation is not used.
