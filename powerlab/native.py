"""Fixed native worker orchestration by Jason Stys.

Functions: executable, invoke. Variables: fixed worker, bounded wire/output and numeric row schema.
Index: docs/CODE_INDEX.md. No shell, arbitrary executable or Python-only success substitution.
"""

import json
import math
import subprocess
import sys
from pathlib import Path

from powerlab.reference import KEYS


def executable() -> Path:
    """Use only this checkout's release worker or the bundled native binary resource."""
    if hasattr(sys, "_MEIPASS"):
        return (
            Path(sys._MEIPASS)
            / "native"
            / ("power_core.exe" if sys.platform == "win32" else "power_core")
        )
    root = Path(__file__).resolve().parents[1] / "native-build"
    return root / ("Release/power_core.exe" if sys.platform == "win32" else "power_core")


def invoke(wire: str) -> list[dict[str, float]]:
    """Execute bounded stdin with timeout; reject failed processes, malformed shapes and nonfinite data."""
    if len(wire.encode()) > 32768:
        raise ValueError("Worker input exceeds 32 KiB")
    worker = executable()
    if not worker.is_file():
        raise RuntimeError("Native worker missing; run python tools/build_native.py")
    try:
        result = subprocess.run(
            [str(worker)], input=wire.encode("ascii"), capture_output=True, check=True, timeout=5
        )
        if len(result.stdout) > 8_388_608:
            raise ValueError("Worker output exceeds 8 MiB")
        data = json.loads(result.stdout)
        if not isinstance(data, list) or not 1 <= len(data) <= 3600:
            raise ValueError("Worker row count")
        for row in data:
            if (
                not isinstance(row, dict)
                or set(row) != set(KEYS)
                or any(
                    type(value) not in (int, float) or abs(value) > 1e9 or not math.isfinite(value)
                    for value in row.values()
                )
            ):
                raise ValueError("Worker numeric row schema")
        return data
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        raise RuntimeError("Native worker failed or returned invalid evidence") from error
