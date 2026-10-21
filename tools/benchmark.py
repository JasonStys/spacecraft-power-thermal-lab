"""Reviewed numerical contracts and descriptive runtime observations by Jason Stys.

Function: main. Variables: fixed reference totals, declared tolerances, timings and Python allocation peak.
No hard realtime/RSS/flight-accuracy claims; index: docs/CODE_INDEX.md.
"""

import argparse
import json
import math
import statistics
import time
import tracemalloc
from pathlib import Path

from powerlab.engine import SCENARIOS, Settings, build_run, canonical


def main() -> None:
    """Check nine reviewed numerical contracts, then describe this machine's IPC+verification workload."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    cases = [
        {"scenario": name, "sample_count": len(run["samples"]), "totals": run["totals"]}
        for name in SCENARIOS
        for run in [build_run(Settings(name))]
    ]
    path = Path("docs/reports/benchmark.json")
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            canonical(
                {
                    "schema": 1,
                    "absolute_tolerance": 1e-6,
                    "relative_tolerance": 1e-8,
                    "cases": cases,
                }
            )
        )
    expected = json.loads(path.read_bytes())
    assert len(expected["cases"]) == len(cases)
    assert (
        expected["schema"] == 1
        and expected["absolute_tolerance"] == 1e-6
        and expected["relative_tolerance"] == 1e-8
    )
    for actual, reference in zip(cases, expected["cases"], strict=True):
        assert (
            actual["scenario"] == reference["scenario"]
            and actual["sample_count"] == reference["sample_count"]
        )
        assert set(actual["totals"]) == set(reference["totals"])
        for key, value in actual["totals"].items():
            assert math.isclose(value, reference["totals"][key], rel_tol=1e-8, abs_tol=1e-6), key
    timings = []
    tracemalloc.start()
    for _ in range(15):
        start = time.perf_counter()
        build_run()
        timings.append((time.perf_counter() - start) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(
        f"Nine numerical contracts passed (abs 1e-6, rel 1e-8); median {statistics.median(timings):.3f} ms; Python traced peak {peak} bytes (includes IPC/reference/tracing; not native RSS or a realtime bound)"
    )


if __name__ == "__main__":
    main()
