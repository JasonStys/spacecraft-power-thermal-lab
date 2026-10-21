"""Independent dictionary-based electrical/thermal reference by Jason Stys.

Functions: simulate, radial. Variables: independently allocated flows, RK4 stages and state history.
Exact lines: docs/CODE_INDEX.md. Not a fallback when the required native worker is unavailable.
"""

from powerlab.model import Case

KEYS = (
    "time_s",
    "dt_s",
    "solar_w",
    "requested_w",
    "served_w",
    "unserved_w",
    "charge_in_w",
    "discharge_bus_w",
    "battery_loss_w",
    "spill_w",
    "energy_wh",
    "temperature_k",
    "heat_in_w",
    "radiation_w",
    "electric_residual_w",
    "thermal_residual_w",
    "base_served_w",
    "heater_served_w",
    "payload_served_w",
    "shed_requested_w",
    "heater_on",
    "payload_enabled",
    "solar_flux_w_m2",
    "payload_requested_w",
)


def simulate(case: Case, step: int, policy: int, heater: int) -> list[dict[str, float]]:
    """Replay average electrical allocation and RK4 stages using separate Python state/flow structures."""
    c = case.config
    state = {
        "energy": c.battery_wh * c.initial_soc,
        "temperature": c.initial_temp_k,
        "time": 0.0,
        "heater": False,
        "payload": True,
    }
    result = []

    def radial(temperature: float) -> float:
        """Outward grey-body radiation to the fixed ideal sink, in watts, using SI kelvin."""
        return c.emissivity * c.radiator_area_m2 * 5.670374419e-8 * (temperature**4 - c.sink_k**4)

    for segment in case.segments:
        for elapsed in range(0, segment.duration_s, step):
            dt = float(min(step, segment.duration_s - elapsed))
            before_e, before_t = float(state["energy"]), float(state["temperature"])
            if policy:
                if before_e / c.battery_wh <= c.reserve_off:
                    state["payload"] = False
                elif before_e / c.battery_wh >= c.reserve_on:
                    state["payload"] = True
            if heater:
                if before_t <= c.heater_on_k:
                    state["heater"] = True
                elif before_t >= c.heater_off_k:
                    state["heater"] = False
            components = [
                c.base_load_w,
                c.heater_w if state["heater"] else 0,
                segment.payload_w if state["payload"] else 0,
            ]
            requested = sum(components)
            solar = segment.solar_flux_w_m2 * c.solar_area_m2 * c.solar_efficiency
            flows = {"charge": 0.0, "discharge": 0.0, "spill": 0.0, "loss": 0.0}
            if solar >= requested:
                flows["charge"] = min(
                    solar - requested,
                    c.charge_limit_w,
                    (c.battery_wh - before_e) * 3600 / (dt * c.charge_efficiency),
                )
                flows["spill"] = solar - requested - flows["charge"]
                flows["loss"] = flows["charge"] * (1 - c.charge_efficiency)
            else:
                flows["discharge"] = min(
                    requested - solar,
                    c.discharge_limit_w,
                    before_e * 3600 * c.discharge_efficiency / dt,
                )
                flows["loss"] = flows["discharge"] / c.discharge_efficiency - flows["discharge"]
            remaining = min(requested, solar + flows["discharge"])
            delivered = []
            for component in components:
                delivered.append(min(component, max(0.0, remaining)))
                remaining -= delivered[-1]
            served = sum(delivered)
            after_e = min(
                c.battery_wh,
                max(
                    0,
                    before_e
                    + dt
                    / 3600
                    * (
                        flows["charge"] * c.charge_efficiency
                        - flows["discharge"] / c.discharge_efficiency
                    ),
                ),
            )
            heat = (
                segment.solar_flux_w_m2 * c.projected_area_m2 * c.absorptivity
                + c.external_heat_w
                + sum(
                    power * fraction
                    for power, fraction in zip(delivered, (0.9, 1.0, 0.6), strict=True)
                )
                + flows["loss"]
            )
            stages: list[float] = []
            outgoing = []
            for fraction in (0.0, 0.5, 0.5, 1.0):
                sample_t = before_t + (stages[-1] if stages else 0) * dt * fraction
                outgoing.append(radial(sample_t))
                stages.append((heat - outgoing[-1]) / c.heat_capacity_j_k)
            weights = (1, 2, 2, 1)
            after_t = before_t + dt * sum(k * w for k, w in zip(stages, weights, strict=True)) / 6
            radiation = sum(r * w for r, w in zip(outgoing, weights, strict=True)) / 6
            if not 100 <= after_t <= 450:
                raise ValueError("Reference outside numerical domain")
            state["time"] += dt
            values = [
                state["time"],
                dt,
                solar,
                requested,
                served,
                requested - served,
                flows["charge"],
                flows["discharge"],
                flows["loss"],
                max(0.0, flows["spill"]),
                after_e,
                after_t,
                heat,
                radiation,
                solar - served - flows["spill"] - flows["loss"] - (after_e - before_e) * 3600 / dt,
                heat - radiation - c.heat_capacity_j_k * (after_t - before_t) / dt,
                *delivered,
                segment.payload_w - components[2],
                float(state["heater"]),
                float(state["payload"]),
                segment.solar_flux_w_m2,
                components[2],
            ]
            result.append(dict(zip(KEYS, values, strict=True)))
            state["energy"], state["temperature"] = after_e, after_t
    return result
