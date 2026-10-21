# Model, units and interpretation

Author: Jason Stys. All spacecraft values and illumination/load profiles are invented. The only adopted universal physical constant is the rounded Stefan–Boltzmann value described below. Verification of these equations is **not** validation of real spacecraft or batteries.

## State, inputs and interval order

State is chemical battery energy E (Wh), one body temperature T (K), two hysteresis booleans and elapsed seconds. Input segments impose constant incident solar flux (W/m²) and scientific load request (W) for integer durations. They do not predict eclipses or attitude. The array and solar-absorbing body surface are distinct external surfaces.

Each interval:

1. Clip the chosen 1/5/10 second step at the next segment boundary.
2. At its **start**, update reserve policy and heater-request hysteresis from prior E/T. Initial heater request is off; initial science is enabled. Within a deadband, retain that state.
3. Calculate available solar power and requested loads, then bounded average battery charge/discharge flows. Saturation is averaged over this interval, not localized to an exact event time.
4. Allocate actual served power in order: housekeeping, requested heater, then requested science.
5. Update chemical battery energy; compute body heat from **actual**, not merely requested, loads and battery losses.
6. Hold that interval's heat input constant and advance the single-body temperature with four-stage RK4. Record its corresponding weighted outward radiation average.
7. Record interval-average powers and **end-of-interval** states. Check numerical domain and both energy ledgers before releasing evidence.

Reserve-aware policy disables science at SOC≤`reserve_off` and enables it at SOC≥`reserve_on`; otherwise the previous state persists. Always-requested policy never intentionally sheds science. The thermostat requests heat at T≤`heater_on_k`, switches off at T≥`heater_off_k` and otherwise retains its state. Disabling the thermostat forces an initially off request throughout the run. Requesting heat does not guarantee enough electrical supply.

## Electrical equations

Let h be interval seconds, Psolar=flux×solar_area×solar_efficiency, D the sum of requests **after policy**, ηc/ηd efficiencies and Pc/Pd charge/discharge limits.

```text
charge_in_W = min(max(Psolar-D,0), Pc, (capacity_Wh-E)*3600/(ηc*h))
discharge_bus_W = min(max(D-Psolar,0), Pd, E*3600*ηd/h)
served_W = min(D, Psolar+discharge_bus_W)
spill_W = max(Psolar-served_W-charge_in_W,0)
battery_loss_W = charge_in_W*(1-ηc) + discharge_bus_W*(1/ηd-1)
E_next = clamp(E + (ηc*charge_in_W-discharge_bus_W/ηd)*h/3600, 0, capacity_Wh)
```

Charge and discharge are mutually exclusive in this algebraic model. Conversion loss becomes body heat. Spilled electrical power and array conversion losses are rejected **outside** the modeled body. Housekeeping and science dissipate 90% and 60% of their actual served powers inside the body; a served heater dissipates 100%. These fractions are explicit invented assumptions, not measured efficiencies.

The independently recomputed electrical residual is:

`Psolar - served_W - spill_W - battery_loss_W - 3600*(E_next-E)/h`.

Its gate is absolute ≤1e−6 W. This is chemical-energy accounting, not a voltage/current/impedance or battery-management model. Low SOC can starve housekeeping after all available supply is exhausted. Intentional shed energy is original scientific request minus post-policy request; **unserved** is post-policy request minus actual served. Do not conflate them when comparing policies.

## Thermal equations and integration

```text
Qin_W = flux*projected_body_area*absorptivity + imposed_external_heat_W
        + 0.9*base_served_W + heater_served_W + 0.6*science_served_W + battery_loss_W
Qrad_W(T) = emissivity*radiator_area*σ*(T^4 - sink_K^4)
dT/dt = (Qin_W - Qrad_W(T))/heat_capacity_J_per_K
```

σ=5.670374419×10⁻⁸ W m⁻² K⁻⁴ is a truncated numerical value from [NIST/CODATA](https://physics.nist.gov/cgi-bin/cuu/Value?sigma%7Csearch_for=stefan+boltzmann). `external_heat_w` is a supplied lumped environmental term; no albedo/planetshine geometry is calculated. A 0 K sink is allowed only as an ideal analytic test case, not a physically achievable environment.

Classic RK4 uses k1=f(T), k2=f(T+h·k1/2), k3=f(T+h·k2/2), k4=f(T+h·k3), then Tnext=T+h(k1+2k2+2k3+k4)/6. Radiation is independently accumulated with the same stage weights. The thermal residual is `Qin - Qrad_RK4_average - C*(Tnext-T)/h`, with the same absolute 1e−6 W gate. This checks integration bookkeeping; using the same quadrature does not make it an independent physical validation.

All native outputs are compared against a separate Python implementation using relative 1e−10 and absolute 1e−8 tolerances. Failed comparisons withhold evidence. Published reports round numerical fields to nine decimal places; displayed residuals can round to zero even when raw residuals are nonzero. Benchmarks compare reviewed summary values with absolute 1e−6 and relative 1e−8 tolerances across compilers.

Analytic tests isolate constant discharge, constant heat with zero emissivity, and radiation-only cooling to an ideal 0 K sink. For radiation-only cooling, `T(t)=(T0^-3 + 3*emissivity*area*σ*t/C)^(-1/3)`. Timestep refinement checks the latter case. This convergence result does not guarantee exact discontinuous-policy switch times or convergence for arbitrary unsupported physics.

## Flags and limits

The hard **numerical** domain is 100–450 K; leaving it aborts rather than extrapolating a plausible result. Input bounds are in [API](API.md). The configurable min/max temperature band is an educational marker, not a real operational or survival rating. `outside_limit_samples` counts sampled interval endpoints only, excluding an initial out-of-band state from that count. Temperature min/max summaries include the initial state and sampled endpoints, not unsampled continuous extrema. No duration-outside-band or real-safety probability is calculated.

The visual curves connect all modeled samples; power curves show interval averages. A linear connection is a presentation choice, not additional simulated substeps. The replay starts at the first interval's end; its charts include an explicit initial point for battery/temperature.

## Primary context

[NASA small-spacecraft power overview](https://www.nasa.gov/smallsat-institute/sst-soa/power-subsystems/) motivates separating generation, storage and distribution. [NASA thermal overview](https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/) motivates explicit absorbed/generated/stored/rejected heat. These references are context—not calibration datasets, endorsements or certifications. No NASA prose, artwork, hardware configuration or mission measurements are bundled.

Omitted physics includes spatial gradients, contact conduction networks, temperature-dependent battery efficiency, chemistry, cell imbalance, voltage, degradation, thermal runaway, real radiator view factors, attitude/orbits, radiation damage, uncertainty distributions and hardware control. Do not use this tool for component sizing, charging real cells, mission decisions or safety determinations.
