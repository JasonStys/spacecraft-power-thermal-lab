"""Per-load service interruption evidence by Jason Stys.

Function: service_ledger. Variables: interval-average requests, delivered watts and bounded episodes.
Intentional shedding is separate from unmet requested load. Exact lines: docs/CODE_INDEX.md.
"""

from typing import Any

from powerlab.model import Config


def service_ledger(rows: list[dict[str, float]], config: Config) -> dict[str, Any]:
    """Integrate component Wh and group consecutive shortfalls without interpolating.

    Boundaries use interval edges, not sampled thermal endpoints. A final interrupted interval
    is right-censored; resumed means no material shortfall in the next simulated interval.
    """
    result: dict[str, Any] = {"components": [], "science_shedding": []}
    for component in ("housekeeping", "heater", "science", "intentional-science-shedding"):
        demand_wh = served_wh = shortfall_wh = 0.0
        active: dict[str, Any] | None = None
        episodes = []
        for row in rows:
            demand, served = (
                (config.base_load_w, row["base_served_w"])
                if component == "housekeeping"
                else (config.heater_w * row["heater_on"], row["heater_served_w"])
                if component == "heater"
                else (row["payload_requested_w"], row["payload_served_w"])
                if component == "science"
                else (row["shed_requested_w"], 0.0)
            )
            deficit = max(0.0, demand - served)
            hours = row["dt_s"] / 3600
            demand_wh += demand * hours
            served_wh += served * hours
            shortfall_wh += deficit * hours
            if deficit > 1e-8:
                if active is None:
                    active = {
                        "start_s": row["time_s"] - row["dt_s"],
                        "end_s": row["time_s"],
                        "energy_wh": 0.0,
                        "peak_w": 0.0,
                        "right_censored": True,
                    }
                active["end_s"] = row["time_s"]
                active["energy_wh"] += deficit * hours
                active["peak_w"] = max(active["peak_w"], deficit)
            elif active is not None:
                active["right_censored"] = False
                episodes.append(active)
                active = None
        if active is not None:
            episodes.append(active)
        if component == "intentional-science-shedding":
            result["science_shedding"] = episodes
        else:
            result["components"].append(
                {
                    "name": component,
                    "requested_wh": demand_wh,
                    "served_wh": served_wh,
                    "unserved_wh": shortfall_wh,
                    "interruptions": episodes,
                }
            )
    return result
