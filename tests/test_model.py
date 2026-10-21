"""Strict numeric envelopes and worker failure boundaries by Jason Stys.

Functions: document, test_* contracts. Variables: invalid quantities, raw protocol, fake outputs.
No arbitrary downloaded programs execute; exact line locations: docs/CODE_INDEX.md.
"""

import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from powerlab.engine import Settings, build_import, fixture
from powerlab.model import BOUNDS, load_case, parse_case, wire
from powerlab.native import executable, invoke
from powerlab.reference import KEYS


def document():
    """Return an independent mutable strict JSON document from an invented profile."""
    return fixture("day-night-cycle").document()


@pytest.mark.parametrize("key", BOUNDS)
@pytest.mark.parametrize(
    "bad",
    [True, None, "5", math.nan, math.inf, -1, 10**1000],
    ids=["bool", "none", "string", "nan", "inf", "negative", "huge-integer"],
)
def test_parameter_types_ranges(key, bad):
    """All physical parameters reject invalid types and huge/nonfinite numbers without OverflowError."""
    value = document()
    value["config"][key] = bad
    with pytest.raises(ValueError):
        parse_case(value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", True),
        ("schema", 2),
        ("name", "<script>"),
        ("name", "x" * 49),
        ("config", {}),
        ("segments", []),
        ("segments", {}),
        ("segments", [{}]),
        ("extra", 1),
    ],
)
def test_root_schema(field, value):
    """Complete root and nested schemas reject unknown/missing fields and empty workloads."""
    case = document()
    case[field] = value
    with pytest.raises(ValueError):
        parse_case(case)


@pytest.mark.parametrize(
    "field,value",
    [
        ("duration_s", True),
        ("duration_s", 1.0),
        ("duration_s", 0),
        ("duration_s", 3601),
        ("solar_flux_w_m2", 2001),
        ("payload_w", 151),
        ("extra", 1),
    ],
)
def test_segment_schema(field, value):
    """Segment bounds reject coercion and unsupported units/keys instead of reinterpretation."""
    case = document()
    case["segments"][0][field] = value
    with pytest.raises(ValueError):
        parse_case(case)


def test_thresholds_duration_and_counts():
    """Reversed thresholds and workloads exceeding record/time caps fail before simulation."""
    for left, right in [
        ("reserve_off", "reserve_on"),
        ("heater_on_k", "heater_off_k"),
        ("min_temp_k", "max_temp_k"),
    ]:
        case = document()
        case["config"][left] = case["config"][right]
        with pytest.raises(ValueError):
            parse_case(case)
    for records in (
        [{"duration_s": 1, "solar_flux_w_m2": 0, "payload_w": 0}] * 33,
        [{"duration_s": 3600, "solar_flux_w_m2": 0, "payload_w": 0}] * 2,
    ):
        case = document()
        case["segments"] = records
        with pytest.raises(ValueError):
            parse_case(case)


def test_file_limits_duplicates_encoding_and_import(tmp_path):
    """Input bounds cover duplicate keys, malformed UTF-8/nesting and truthful local provenance."""
    path = tmp_path / "input.json"
    path.write_text(json.dumps(document()), encoding="utf-8")
    imported = build_import(path, Settings(battery=20))
    assert imported["input"]["config"]["battery_wh"] == 40
    assert imported["provenance"]["source"].startswith("unverified local")
    for body in (
        b"{}",
        b'{"schema":1,"schema":1}',
        b"\xff",
        b"[" * 1100 + b"]" * 1100,
        b" " * 32769,
    ):
        path.write_bytes(body)
        with pytest.raises(ValueError):
            load_case(path)


@pytest.mark.parametrize("step,policy,heater", [(True, 0, 1), (2, 0, 1), (5, True, 1), (5, 0, 1.0)])
def test_wire_controls(step, policy, heater):
    """Direct wire callers receive the same strict type/range controls as the UI."""
    with pytest.raises(ValueError):
        wire(fixture("day-night-cycle"), step, policy, heater)


def test_missing_timeout_bundled_and_unknown(monkeypatch, tmp_path):
    """Missing/failed workers never return reference-only success; bundled paths remain fixed."""
    monkeypatch.setattr("powerlab.native.executable", lambda: tmp_path / "missing")
    with pytest.raises(RuntimeError, match="missing"):
        invoke("POWER1 5 0 1\n")
    monkeypatch.setattr("powerlab.native.executable", lambda: Path(__file__))

    def timeout(*args, **kwargs):
        """Model a worker deadline without changing the timeout or spawning untrusted code."""
        raise subprocess.TimeoutExpired("owned-worker", 5)

    monkeypatch.setattr("powerlab.native.subprocess.run", timeout)
    with pytest.raises(RuntimeError):
        invoke("POWER1 5 0 1\n")
    monkeypatch.setattr("powerlab.native.sys._MEIPASS", str(tmp_path), raising=False)
    assert executable().parent == tmp_path / "native"
    with pytest.raises(ValueError):
        fixture("unknown")


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"[]",
        b"not-json",
        b"[{}]",
        b"[1]",
        b"x" * 8388609,
        json.dumps([{k: math.inf for k in KEYS}]).encode(),
        json.dumps([{k: 10**1000 for k in KEYS}]).encode(),
    ],
    ids=["object", "empty", "json", "missing", "row", "oversized", "infinity", "huge-number"],
)
def test_worker_result_contract(monkeypatch, body):
    """Invalid numeric shape, size and finite checks produce controlled bridge errors."""
    monkeypatch.setattr("powerlab.native.executable", lambda: Path(__file__))
    monkeypatch.setattr(
        "powerlab.native.subprocess.run", lambda *args, **kwargs: SimpleNamespace(stdout=body)
    )
    with pytest.raises(RuntimeError):
        invoke("POWER1 5 0 1\n")


@pytest.mark.parametrize(
    "bad",
    ["", "POWER1 2 0 1\n", "x" * 32769, "POWER1 5.0 0 1\n", "POWER1 5 0 1\nP nan\n"],
    ids=["empty", "step", "oversized", "integer", "parameters"],
)
def test_malformed_native_envelope(bad):
    """Actual native process rejects malformed headers/input without partial successful JSON."""
    with pytest.raises((ValueError, RuntimeError)):
        invoke(bad)


def test_actual_native_parameter_parser():
    """Native numeric bounds and trailing-data/count checks execute against the compiled worker."""
    baseline = wire(fixture("day-night-cycle"), 5, 0, 1)
    header, parameters, *segments = baseline.splitlines()
    words = parameters.split()
    for i in range(1, len(words)):
        bad = words.copy()
        bad[i] = "nan"
        with pytest.raises(RuntimeError):
            invoke(header + "\n" + " ".join(bad) + "\n" + "\n".join(segments) + "\n")
    for tail in (
        "S 0 0 0\n",
        "S 3601 0 0\n",
        "S 1 0 151\n",
        "S 1 2001 0\n",
        "S 3600 0 0\n" * 2,
        "S 1 0 0\n" * 33,
        "X 1 2 3\n",
    ):
        with pytest.raises(RuntimeError):
            invoke(header + "\n" + parameters + "\n" + tail)
    for controls in ("POWER1 5 2 1", "POWER1 5 0 2", "POWER1 0 0 1"):
        with pytest.raises(RuntimeError):
            invoke(baseline.replace(header, controls))
