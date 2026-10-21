"""Strict SI parameter/profile contracts by Jason Stys.

Types: Config, Segment, Case. Functions: validate, parse_case, load_case, wire, unique_object.
Variables/fields and exact locations: docs/CODE_INDEX.md. All profiles are invented.
"""

import json
import math
import re
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

BOUNDS = {
    "solar_area_m2": (0, 1),
    "solar_efficiency": (0, 0.5),
    "battery_wh": (1, 200),
    "initial_soc": (0, 1),
    "charge_efficiency": (0.1, 1),
    "discharge_efficiency": (0.1, 1),
    "charge_limit_w": (0, 200),
    "discharge_limit_w": (0, 200),
    "heat_capacity_j_k": (1000, 10000),
    "radiator_area_m2": (0, 1),
    "emissivity": (0, 1),
    "absorptivity": (0, 1),
    "projected_area_m2": (0, 1),
    "sink_k": (0, 50),
    "external_heat_w": (0, 100),
    "base_load_w": (0, 100),
    "heater_w": (0, 100),
    "heater_on_k": (180, 350),
    "heater_off_k": (180, 360),
    "reserve_off": (0, 1),
    "reserve_on": (0, 1),
    "initial_temp_k": (180, 360),
    "min_temp_k": (180, 350),
    "max_temp_k": (180, 400),
}


@dataclass(frozen=True)
class Config:
    """Invented fixed body/battery profile; dimensioned fields and allowed ranges are in BOUNDS."""

    solar_area_m2: float = 0.2
    solar_efficiency: float = 0.28
    battery_wh: float = 40
    initial_soc: float = 0.6
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9
    charge_limit_w: float = 30
    discharge_limit_w: float = 40
    heat_capacity_j_k: float = 5000
    radiator_area_m2: float = 0.08
    emissivity: float = 0.8
    absorptivity: float = 0.2
    projected_area_m2: float = 0.05
    sink_k: float = 3
    external_heat_w: float = 5
    base_load_w: float = 8
    heater_w: float = 6
    heater_on_k: float = 275
    heater_off_k: float = 280
    reserve_off: float = 0.3
    reserve_on: float = 0.5
    initial_temp_k: float = 285
    min_temp_k: float = 260
    max_temp_k: float = 320


@dataclass(frozen=True)
class Segment:
    """Piecewise-constant imposed environment, duration seconds, incident flux W/m² and science W."""

    duration_s: int
    solar_flux_w_m2: float
    payload_w: float


@dataclass(frozen=True)
class Case:
    """Immutable strict schema-1 synthetic profile; source settings are separate finite controls."""

    name: str
    config: Config
    segments: tuple[Segment, ...]

    def document(self) -> dict[str, Any]:
        """Produce genuine JSON lists and complete parameters without host paths or trusted-data claims."""
        return {
            "schema": 1,
            "name": self.name,
            "config": asdict(self.config),
            "segments": [asdict(segment) for segment in self.segments],
        }


def bounded(value: Any, low: float, high: float) -> float:
    """Accept finite JSON numbers only, never booleans, strings, NaN or infinity."""
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        raise ValueError("Invalid finite quantity")
    return float(value)


def integer(value: Any, low: int, high: int) -> int:
    """Require actual bounded integers instead of coercing booleans or fractional values."""
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Invalid integer")
    return value


def exact(value: Any, names: set[str]) -> dict[str, Any]:
    """Reject extra/missing fields rather than silently ignoring unsupported parameters."""
    if not isinstance(value, dict) or set(value) != names:
        raise ValueError("Unexpected fields")
    return value


def parse_case(value: Any) -> Case:
    """Validate complete profile bounds, hysteresis order, counts and duration before native execution."""
    obj = exact(value, {"schema", "name", "config", "segments"})
    integer(obj["schema"], 1, 1)
    if not isinstance(obj["name"], str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,47}", obj["name"]
    ):
        raise ValueError("Invalid name")
    parameters = exact(obj["config"], set(BOUNDS))
    config = Config(**{key: bounded(parameters[key], *limits) for key, limits in BOUNDS.items()})
    if (
        config.heater_on_k >= config.heater_off_k
        or config.reserve_off >= config.reserve_on
        or config.min_temp_k >= config.max_temp_k
    ):
        raise ValueError("Invalid threshold order")
    if not isinstance(obj["segments"], list) or not 1 <= len(obj["segments"]) <= 32:
        raise ValueError("Invalid segment count")
    segments = []
    for row in obj["segments"]:
        row = exact(row, {"duration_s", "solar_flux_w_m2", "payload_w"})
        segments.append(
            Segment(
                integer(row["duration_s"], 1, 3600),
                bounded(row["solar_flux_w_m2"], 0, 2000),
                bounded(row["payload_w"], 0, 150),
            )
        )
    if sum(segment.duration_s for segment in segments) > 3600:
        raise ValueError("Duration exceeds 3600 seconds")
    return Case(obj["name"], config, tuple(segments))


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON object keys to prevent last-write-wins reinterpretation."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def load_case(path: Path) -> Case:
    """Read at most 32 KiB plus one sentinel; malformed UTF-8/nesting errors are controlled."""
    with path.open("rb") as source:
        body = source.read(32769)
    if len(body) > 32768:
        raise ValueError("Input exceeds 32 KiB")
    try:
        return parse_case(json.loads(body.decode("utf-8"), object_pairs_hook=unique_object))
    except (UnicodeError, RecursionError) as error:
        raise ValueError("Invalid JSON envelope") from error


def wire(case: Case, step: int, policy: int, heater: int) -> str:
    """Encode a validated finite numeric envelope; payloads never select paths, URLs or commands."""
    parse_case(case.document())
    if type(step) is not int or step not in (1, 5, 10):
        raise ValueError("Invalid integration step")
    integer(policy, 0, 1)
    integer(heater, 0, 1)
    lines = [
        f"POWER1 {step} {policy} {heater}",
        "P " + " ".join(str(getattr(case.config, field.name)) for field in fields(Config)),
    ]
    lines.extend(
        f"S {segment.duration_s} {segment.solar_flux_w_m2} {segment.payload_w}"
        for segment in case.segments
    )
    return "\n".join(lines) + "\n"
