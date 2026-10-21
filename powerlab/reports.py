"""Deterministic inert reports and opt-in immutable SQLite history by Jason Stys.

Functions: export_report, save_history. Variables: fixed CSV fields, schema, content hash.
Exact lines and parameters: docs/CODE_INDEX.md. No HTML scripts or external report resources.
"""

import csv
import hashlib
import html
import io
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from powerlab.engine import RESOURCES, canonical


def export_report(run: dict[str, Any], format_name: str) -> tuple[bytes, str]:
    """Render full JSON/input, dimensioned numeric interval CSV or escaped static HTML."""
    if format_name == "json":
        return canonical(run), "application/json"
    if format_name == "input":
        return canonical(run["input"]), "application/json"
    if format_name == "csv":
        buffer = io.StringIO(newline="")
        keys = [
            "time_s",
            "dt_s",
            "solar_w",
            "requested_w",
            "served_w",
            "unserved_w",
            "energy_wh",
            "temperature_k",
            "heat_in_w",
            "radiation_w",
            "spill_w",
            "battery_loss_w",
            "heater_served_w",
            "payload_served_w",
            "shed_requested_w",
        ]
        writer = csv.DictWriter(buffer, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row[key] for key in keys} for row in run["samples"])
        return buffer.getvalue().encode(), "text/csv"
    if format_name != "html":
        raise ValueError("Unsupported report format")
    escaped = html.escape(canonical(run).decode())
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Power Thermal Evidence by Jason Stys</title><h1>Spacecraft Power Thermal Lab</h1><p>By Jason Stys. Offline educational evidence, not flight-qualified analysis or measured telemetry.</p><p>Includes full synthetic parameters, imposed environments, interval flows, state samples, energy-balance checks and limitations.</p><pre>'
        + escaped
        + "</pre></html>"
    )
    return page.encode(), "text/html"


def save_history(path: Path, run: dict[str, Any]) -> None:
    """Verify full report identity, insert idempotently, and refuse pruning/updates after 100 reports."""
    content = dict(run)
    identity = content.pop("id", None)
    if not isinstance(identity, str) or hashlib.sha256(canonical(content)).hexdigest() != identity:
        raise ValueError("Report hash mismatch")
    schema = (RESOURCES / "history.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(schema)
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM runs WHERE id=?", (identity,)).fetchone():
            return
        if connection.execute("SELECT count(*) FROM runs").fetchone()[0] >= 100:
            raise ValueError("History full; choose a new local history path")
        connection.execute(
            "INSERT INTO runs(id,scenario,report_json) VALUES(?,?,?)",
            (identity, run["name"], canonical(run).decode()),
        )
