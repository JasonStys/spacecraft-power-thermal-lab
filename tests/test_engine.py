"""Cross-language, analytic, conservation and policy tests by Jason Stys.

Functions: test_* contracts. Variables: all 324 finite controls, hand-derived cases, random valid profiles.
Actual C++ execution is mandatory; exact definition/variable lines: docs/CODE_INDEX.md.
"""

import itertools
import math
from dataclasses import replace

import pytest
from hypothesis import given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from powerlab.engine import (
    CHOICES,
    SCENARIOS,
    Settings,
    analyze,
    build_run,
    canonical,
    fixture,
    run_id,
)
from powerlab.model import Case, Config, Segment
from powerlab.reference import simulate


@pytest.mark.parametrize(
    "scenario,battery,policy,step,heater", list(itertools.product(SCENARIOS, *CHOICES.values()))
)
def test_grid(scenario, battery, policy, step, heater):
    """Every finite UI combination agrees with independent Python and satisfies state/ledger bounds."""
    run = build_run(Settings(scenario, battery, policy, step, heater))
    assert run["id"] == run_id(run) and len(run["samples"]) <= 3600
    for row in run["samples"]:
        assert 0 <= row["energy_wh"] <= battery
        assert row["served_w"] <= row["requested_w"] + 1e-8
        assert row["unserved_w"] >= -1e-8 and row["spill_w"] >= -1e-8
        assert max(abs(row["electric_residual_w"]), abs(row["thermal_residual_w"])) <= 1e-6


def test_analytic_discharge_adiabatic_and_radiation():
    """Closed-form battery, constant heat and separable radiation references constrain both models."""
    c = replace(
        Config(),
        emissivity=0,
        external_heat_w=0,
        base_load_w=10,
        solar_area_m2=0,
        battery_wh=20,
        initial_soc=0.5,
        discharge_efficiency=0.5,
    )
    result = analyze(
        Case("analytic", c, (Segment(360, 0, 0),)), Settings(heater=0), "hand-derived test"
    )
    assert result["samples"][-1]["energy_wh"] == pytest.approx(8, abs=1e-8)
    c = replace(c, base_load_w=0, external_heat_w=10, heat_capacity_j_k=1000)
    result = analyze(Case("heat", c, (Segment(100, 0, 0),)), Settings(heater=0), "hand-derived")
    assert result["samples"][-1]["temperature_k"] == pytest.approx(286, abs=1e-8)
    case = fixture("isolated-cooling")
    errors = []
    for step in (10, 5, 1):
        result = analyze(case, Settings(step=step, heater=0), "analytic cooling")
        c = case.config
        exact = (
            c.initial_temp_k**-3
            + 3 * c.emissivity * c.radiator_area_m2 * 5.670374419e-8 * 1200 / c.heat_capacity_j_k
        ) ** (-1 / 3)
        errors.append(abs(result["samples"][-1]["temperature_k"] - exact))
    assert errors[0] < 1e-5 and errors[1] <= errors[0] and errors[-1] <= errors[0]


def test_saturation_allocation_and_policy_tradeoff():
    """Empty/full edges, actual heater starvation and science/housekeeping tradeoffs are observable."""
    empty = build_run(Settings("battery-empty"))
    full = build_run(Settings("battery-full"))
    assert empty["totals"]["unserved_wh"] > 0 and empty["totals"]["final_soc"] > 0
    assert full["totals"]["final_soc"] == 1 and full["totals"]["spill_wh"] > 0
    first = build_run(Settings("heater-contention"))["samples"][0]
    assert first["heater_on"] == 1 and first["base_served_w"] == 8
    assert first["heater_served_w"] == pytest.approx(3.2) and first["payload_served_w"] == 0
    always = build_run(Settings("extended-eclipse", policy=0))
    reserve = build_run(Settings("extended-eclipse", policy=1))
    assert reserve["totals"]["science_shed_wh"] > 0
    assert reserve["totals"]["min_soc"] > always["totals"]["min_soc"]
    assert reserve["totals"]["science_served_wh"] < always["totals"]["science_served_wh"]
    assert reserve["totals"]["unserved_wh"] < always["totals"]["unserved_wh"]


def test_boundary_clipping_and_decision_hysteresis():
    """No step crosses an imposed segment edge; hysteresis starts off inside the deadband."""
    case = Case(
        "edges", replace(Config(), initial_temp_k=278), (Segment(7, 1000, 0), Segment(3, 0, 0))
    )
    result = analyze(case, Settings(step=5), "test")
    assert [(r["time_s"], r["dt_s"], r["solar_flux_w_m2"]) for r in result["samples"]] == [
        (5, 5, 1000),
        (7, 2, 1000),
        (10, 3, 0),
    ]
    assert all(r["heater_on"] == 0 for r in result["samples"])
    case = replace(case, config=replace(case.config, initial_soc=0.3))
    assert analyze(case, Settings(policy=1), "test")["samples"][0]["payload_enabled"] == 0
    case = replace(case, config=replace(case.config, initial_temp_k=275))
    assert analyze(case, Settings(), "test")["samples"][0]["heater_on"] == 1


def test_mismatch_and_conservation_withhold_evidence(monkeypatch):
    """Trace mismatches and an independently failed ledger never return plausible-looking successes."""
    case = fixture("day-night-cycle")
    monkeypatch.setattr("powerlab.engine.simulate", lambda *args: [])
    with pytest.raises(RuntimeError, match="disagreement"):
        build_run()
    rows = simulate(case, 5, 0, 1)
    rows[0]["heat_in_w"] += 0.1
    monkeypatch.setattr("powerlab.engine.simulate", lambda *args: rows)
    monkeypatch.setattr("powerlab.engine.invoke", lambda *args: rows)
    with pytest.raises(RuntimeError, match="Energy balance"):
        build_run()


@pytest.mark.parametrize(
    "key,value",
    [
        ("scenario", []),
        ("scenario", "unknown"),
        ("battery", True),
        ("battery", 40.0),
        ("battery", 41),
        ("step", 0),
        ("policy", 2),
        ("heater", False),
    ],
)
def test_finite_settings(key, value):
    """Settings reject invalid types/coercions and unsupported values before any native process."""
    with pytest.raises(ValueError):
        Settings(**{key: value})


def test_repeatability_and_numeric_domain_failure():
    """Same environment repeats canonical evidence; unsupported thermal states fail explicitly."""
    assert canonical(build_run()) == canonical(build_run())
    case = Case(
        "too-hot",
        replace(
            Config(),
            heat_capacity_j_k=1000,
            base_load_w=0,
            external_heat_w=100,
            radiator_area_m2=0,
            initial_temp_k=360,
        ),
        (Segment(3600, 2000, 0),),
    )
    with pytest.raises(RuntimeError, match="Native worker"):
        analyze(case, Settings(), "outside numerical domain")
    with pytest.raises(ValueError, match="numerical domain"):
        simulate(case, 5, 0, 1)
    with pytest.raises(ValueError):
        canonical({"bad": math.nan})


@hypothesis_settings(max_examples=100, derandomize=True, deadline=None)
@given(
    st.lists(
        st.tuples(st.integers(1, 120), st.integers(0, 1600), st.integers(0, 50)),
        min_size=1,
        max_size=4,
    ),
    st.sampled_from([1, 5, 10]),
    st.integers(0, 1),
    st.integers(0, 1),
    st.integers(0, 100),
)
def test_generated_profiles(records, step, policy, heater, soc):
    """100 generated bounded profiles compare every native/reference state and interval flow."""
    case = Case(
        "generated", replace(Config(), initial_soc=soc / 100), tuple(Segment(*r) for r in records)
    )
    run = analyze(case, Settings(step=step, policy=policy, heater=heater), "generated test")
    assert run["totals"]["duration_s"] == sum(r[0] for r in records)


def test_reference_switching_and_charge_limits():
    """Hot/cold and low/high-SOC cases cover both hysteresis edges and power limits."""
    case = Case(
        "switch",
        replace(
            Config(),
            initial_soc=0.2,
            initial_temp_k=275,
            heat_capacity_j_k=1000,
            external_heat_w=100,
            radiator_area_m2=0,
        ),
        (Segment(200, 1361, 0),),
    )
    result = analyze(case, Settings(policy=1), "test")
    assert result["samples"][0]["heater_on"] == 1 and result["samples"][-1]["heater_on"] == 0
    assert all(r["charge_in_w"] <= case.config.charge_limit_w for r in result["samples"])
    case = replace(case, config=replace(case.config, initial_soc=0.5))
    assert analyze(case, Settings(policy=1), "test")["samples"][0]["payload_enabled"] == 1
