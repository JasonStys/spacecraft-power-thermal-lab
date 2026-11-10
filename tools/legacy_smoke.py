"""Execute owned frozen application acceptance checks by Jason Stys.

Functions: main, read_output. Variables: process, queue, temporary exports and actual HTTP responses.
Only this explicitly supplied newly built bundle is started/stopped. Index: docs/CODE_INDEX.md.
"""

import json

if __package__:
    from .release_contract import require
else:
    from release_contract import require
import queue
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path


def main(executable: Path) -> None:
    """Require notices, a real C++/Python result, reusable input/history and the actual production website."""
    executable = executable.resolve(strict=True)
    require(
        "Vite core license"
        in (executable.parent / "_internal/licenses/vite/LICENSE.md").read_text(encoding="utf-8"),
        "Legacy native acceptance condition failed",
    )
    with tempfile.TemporaryDirectory(prefix="power-smoke-") as directory:
        output = Path(directory) / "report.json"
        subprocess.run(
            [
                str(executable),
                "export",
                "--scenario",
                "extended-eclipse",
                "--policy",
                "1",
                "--output",
                str(output),
                "--history",
                str(Path(directory) / "history.sqlite3"),
            ],
            check=True,
            timeout=30,
        )
        report = json.loads(output.read_bytes())
        require(
            report["totals"]["science_shed_wh"] > 0 and report["totals"]["min_soc"] > 0,
            "Legacy native acceptance condition failed",
        )
        require(
            report["totals"]["max_thermal_residual_w"] < 1e-06,
            "Legacy native acceptance condition failed",
        )
    process = subprocess.Popen(
        [str(executable), "serve", "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def read_output() -> None:
        """Read child startup output off-thread so application startup stays deadline bounded."""
        require(process.stdout is not None, "Legacy native acceptance condition failed")
        for line in process.stdout:
            lines.put(line.strip())

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    try:
        url = ""
        for _ in range(5):
            line = lines.get(timeout=15)
            if line.startswith("http://127.0.0.1:"):
                url = line
                break
        require(url, "Legacy native acceptance condition failed")
        for path in ("api/health", "", "api/run?scenario=heater-contention"):
            with urllib.request.urlopen(url + path, timeout=10) as response:
                body = response.read()
                if path == "":
                    require(
                        b"HELIO" in body and b"/assets/" in body,
                        "Legacy native acceptance condition failed",
                    )
                elif path.startswith("api/run"):
                    require(
                        json.loads(body)["samples"][0]["heater_served_w"] == 3.2,
                        "Legacy native acceptance condition failed",
                    )
                else:
                    require(
                        json.loads(body)["status"] == "ok",
                        "Legacy native acceptance condition failed",
                    )
        print(
            "Frozen app passed: notices, actual C++/Python/energy gates, reserve policy, SQL history, production assets and HTTP analysis"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        reader.join(timeout=3)
        if process.stdout:
            process.stdout.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
