"""Invented cases, cross-language agreement and evidence summaries by Jason Stys.

Types/functions: Settings, fixture, analyze, build_run, build_import, canonical, run_id, catalog.
Variable/field lines: docs/CODE_INDEX.md. Numerical verification is not real-spacecraft validation.
"""

import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from powerlab.model import Case, Config, Segment, load_case, parse_case, wire
from powerlab.native import invoke
from powerlab.reference import KEYS, simulate

RESOURCES = Path(__file__).parent / "resources"
SCENARIOS = {
    "day-night-cycle": "Illumination cycle",
    "extended-eclipse": "Extended darkness",
    "payload-surge": "Scientific payload surge",
    "cold-start": "Cold start",
    "hot-soak": "Hot soak",
    "battery-full": "Full battery / spill",
    "battery-empty": "Empty battery / recovery",
    "isolated-cooling": "Analytic cooling",
    "heater-contention": "Heater power contention",
}
CHOICES = {"battery": (20, 40, 80), "policy": (0, 1), "step": (1, 5, 10), "heater": (0, 1)}
LIMITATIONS = [
    "Invented offline profiles, not measured telemetry, orbital eclipse prediction or flight-qualified analysis.",
    "One isothermal body, ideal fixed sink/geometry, constant efficiencies and averaged electrical flows; not battery electrochemistry, degradation or thermal runaway.",
    "Control decisions are held at interval starts; saturation is step-averaged. Threshold crossings are sampled, not continuous-time extrema or exact switch times.",
    "Separate external array/body surfaces; array losses and spilled bus power are rejected outside the modeled body. No albedo/planetshine geometry, voltage, wiring or heater hardware is simulated.",
    "Model limit flags do not establish real spacecraft safety. Native/reference agreement and analytic checks verify equations, not a real mission's physical validity.",
]


@dataclass(frozen=True)
class Settings:
    """Finite browser controls; imported profiles preserve their own battery size and provenance."""

    scenario: str = "day-night-cycle"
    battery: int = 40
    policy: int = 0
    step: int = 5
    heater: int = 1

    def __post_init__(self) -> None:
        """Reject unknown scenarios, bools, floats and unsupported settings without coercion."""
        if not isinstance(self.scenario, str) or self.scenario not in SCENARIOS:
            raise ValueError("Unknown scenario")
        for key, values in CHOICES.items():
            if type(getattr(self, key)) is not int or getattr(self, key) not in values:
                raise ValueError("Unsupported control")


def fixture(scenario: str) -> Case:
    """Construct explicit synthetic environmental profiles; no NASA data or spacecraft parameters used."""
    config = Config()
    profiles = [(450, 1361, 15), (300, 0, 15), (450, 1361, 25), (300, 0, 15)]
    if scenario == "extended-eclipse":
        profiles = [(120, 1361, 35), (2400, 0, 35), (180, 1361, 15)]
    elif scenario == "payload-surge":
        profiles = [(300, 1361, 15), (600, 1361, 100), (300, 0, 5)]
    elif scenario == "cold-start":
        config = replace(config, initial_temp_k=250, external_heat_w=0)
        profiles = [(600, 0, 15), (600, 1361, 15)]
    elif scenario == "hot-soak":
        config = replace(config, initial_temp_k=310, radiator_area_m2=0.03, external_heat_w=30)
        profiles = [(1200, 2000, 35)]
    elif scenario == "battery-full":
        config = replace(config, initial_soc=1)
        profiles = [(800, 1361, 0)]
    elif scenario == "battery-empty":
        config = replace(config, initial_soc=0)
        profiles = [(600, 0, 15), (600, 1361, 15)]
    elif scenario == "isolated-cooling":
        config = replace(
            config,
            initial_temp_k=340,
            external_heat_w=0,
            base_load_w=0,
            projected_area_m2=0,
            sink_k=0,
            radiator_area_m2=0.15,
            heat_capacity_j_k=1500,
        )
        profiles = [(1200, 0, 0)]
    elif scenario == "heater-contention":
        config = replace(config, initial_temp_k=250, initial_soc=0, external_heat_w=0)
        profiles = [(600, 200, 15)]
    elif scenario != "day-night-cycle":
        raise ValueError("Unknown fixture")
    return parse_case(Case(scenario, config, tuple(Segment(*row) for row in profiles)).document())


def canonical(value: Any) -> bytes:
    """Stable complete ASCII JSON, no timestamps/host paths, NaN/infinity or hidden secret fields."""
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False, ensure_ascii=True) + "\n"
    ).encode()


def run_id(run: dict[str, Any]) -> str:
    """Hash canonical evidence excluding its own id; this identity is not a signature."""
    return hashlib.sha256(
        canonical({key: value for key, value in run.items() if key != "id"})
    ).hexdigest()


def catalog() -> dict[str, Any]:
    """Expose finite choices only; no caller-supplied executable, file, device or network address."""
    return {"scenarios": SCENARIOS, "choices": CHOICES, "defaults": asdict(Settings())}


def analyze(case: Case, settings: Settings, source: str) -> dict[str, Any]:
    """Require actual native/reference agreement and independently audit both SI energy ledgers."""
    rows = invoke(wire(case, settings.step, settings.policy, settings.heater))
    reference = simulate(case, settings.step, settings.policy, settings.heater)
    if len(rows) != len(reference) or any(
        not math.isclose(row[key], expected[key], rel_tol=1e-10, abs_tol=1e-8)
        for row, expected in zip(rows, reference, strict=True)
        for key in KEYS
    ):
        raise RuntimeError("C++/Python disagreement; evidence withheld")
    c = case.config
    previous_e, previous_t = c.battery_wh * c.initial_soc, c.initial_temp_k
    electrical_error = thermal_error = 0.0
    for row in rows:
        h = row["dt_s"]
        electrical_error = max(
            electrical_error,
            abs(
                row["solar_w"]
                - row["served_w"]
                - row["spill_w"]
                - row["battery_loss_w"]
                - (row["energy_wh"] - previous_e) * 3600 / h
            ),
        )
        thermal_error = max(
            thermal_error,
            abs(
                row["heat_in_w"]
                - row["radiation_w"]
                - c.heat_capacity_j_k * (row["temperature_k"] - previous_t) / h
            ),
        )
        previous_e, previous_t = row["energy_wh"], row["temperature_k"]
    if max(electrical_error, thermal_error) > 1e-6:
        raise RuntimeError("Energy balance failed; evidence withheld")
    totals = {
        "duration_s": rows[-1]["time_s"],
        "final_soc": rows[-1]["energy_wh"] / c.battery_wh,
        "min_soc": min([c.initial_soc] + [r["energy_wh"] / c.battery_wh for r in rows]),
        "min_temperature_k": min([c.initial_temp_k] + [r["temperature_k"] for r in rows]),
        "max_temperature_k": max([c.initial_temp_k] + [r["temperature_k"] for r in rows]),
        "max_electric_residual_w": electrical_error,
        "max_thermal_residual_w": thermal_error,
        "outside_limit_samples": sum(
            not c.min_temp_k <= r["temperature_k"] <= c.max_temp_k for r in rows
        ),
    }
    for name, key in {
        "solar_wh": "solar_w",
        "served_wh": "served_w",
        "unserved_wh": "unserved_w",
        "spill_wh": "spill_w",
        "battery_loss_wh": "battery_loss_w",
        "science_served_wh": "payload_served_w",
        "science_shed_wh": "shed_requested_w",
        "heater_served_wh": "heater_served_w",
    }.items():
        totals[name] = sum(row[key] * row["dt_s"] / 3600 for row in rows)
    run: dict[str, Any] = {
        "schema": 1,
        "name": case.name,
        "input": case.document(),
        "settings": asdict(settings),
        "provenance": {
            "author": "Jason Stys",
            "source": source,
            "native": "C++20 bounded RK4 and power allocation",
            "reference": "Independent Python flows/RK4; every sample compared; both energy ledgers audited",
        },
        "limitations": LIMITATIONS,
        "totals": {key: round(value, 9) for key, value in totals.items()},
        "samples": [{key: round(value, 9) for key, value in row.items()} for row in rows],
    }
    run["id"] = run_id(run)
    return run


def build_run(settings: Settings | None = None) -> dict[str, Any]:
    """Build a finite invented scenario, overriding battery capacity with its selected UI control."""
    settings = settings or Settings()
    case = fixture(settings.scenario)
    case = replace(case, config=replace(case.config, battery_wh=settings.battery))
    return analyze(case, settings, "invented built-in profile; no measured spacecraft data")


def build_import(path: Path, settings: Settings) -> dict[str, Any]:
    """Use explicit local parameters exactly; imported capacity is not replaced by a browser preset."""
    return analyze(
        load_case(path), settings, "unverified local synthetic input; not measured telemetry"
    )
