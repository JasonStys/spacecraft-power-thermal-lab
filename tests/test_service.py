"""Independent per-load watt-hour and interruption examples by Jason Stys.

Functions: sample and test_*; variables: hand-set one-hour intervals and exact component budgets.
No native allocation is replaced by this ledger. Definition lines: docs/CODE_INDEX.md.
"""

import math

from powerlab.engine import SCENARIOS, Settings, build_run
from powerlab.model import Config
from powerlab.service import service_ledger


def sample(
    end: float, base: float, heater: float, science: float, shed: float = 0
) -> dict[str, float]:
    """One-hour interval with requested 8W housekeeping, 6W heater and 10W science."""
    return {
        "time_s": end,
        "dt_s": 3600,
        "base_served_w": base,
        "heater_on": 1,
        "heater_served_w": heater,
        "payload_requested_w": 10,
        "payload_served_w": science,
        "shed_requested_w": shed,
    }


def test_manual_energy_recovery_and_end_censoring():
    """Requested/served/deficit Wh integrate exactly and recovery does not erase an earlier deficit."""
    ledger = service_ledger(
        [sample(3600, 4, 0, 0), sample(7200, 8, 6, 10), sample(10800, 8, 6, 5, 7)], Config()
    )
    base, heater, science = ledger["components"]
    assert (base["requested_wh"], base["served_wh"], base["unserved_wh"]) == (24, 20, 4)
    assert base["interruptions"][0] == {
        "start_s": 0,
        "end_s": 3600,
        "energy_wh": 4,
        "peak_w": 4,
        "right_censored": False,
    }
    assert heater["unserved_wh"] == 6
    assert science["unserved_wh"] == 15
    assert science["interruptions"][-1]["right_censored"]
    assert ledger["science_shedding"][0]["energy_wh"] == 7
    assert ledger["science_shedding"][0]["right_censored"]
    assert service_ledger([], Config())["science_shedding"] == []


def test_all_native_cases_reconcile_component_shortfalls_and_shedding():
    """New component accounting independently conserves the already audited aggregate Wh."""
    for scenario in SCENARIOS:
        run = build_run(Settings(scenario=scenario, policy=1))
        assert math.isclose(
            sum(c["unserved_wh"] for c in run["service"]["components"]),
            run["totals"]["unserved_wh"],
            abs_tol=1e-7,
        )
        assert math.isclose(
            sum(e["energy_wh"] for e in run["service"]["science_shedding"]),
            run["totals"]["science_shed_wh"],
            abs_tol=1e-7,
        )
