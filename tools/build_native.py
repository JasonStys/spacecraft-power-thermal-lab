"""Cross-platform C++ build/test orchestration by Jason Stys.

Functions: main, windows_generator. Variables: fixed build roots, CMake flags and compiler version.
No arbitrary compiler/shell commands from HTTP. Exact line inventory: docs/CODE_INDEX.md.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_tool(name: str) -> str:
    """Prefer the hash-locked venv tool; otherwise use an explicitly installed PATH tool."""
    local = Path(sys.executable).parent / (name + ".exe" if sys.platform == "win32" else name)
    if local.is_file():
        return str(local)
    found = shutil.which(name)
    if not found:
        raise SystemExit(f"Missing {name}; install locked development dependencies")
    return found


def windows_generator() -> list[str]:
    """Select the installed official Visual Studio toolchain without modifying global PATH."""
    vswhere = (
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
        / "Microsoft Visual Studio/Installer/vswhere.exe"
    )
    result = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    installation = json.loads(result.stdout)[0]
    major = installation["installationVersion"].split(".")[0]
    generators = {"18": "Visual Studio 18 2026", "17": "Visual Studio 17 2022"}
    if major not in generators:
        raise SystemExit("Visual Studio 2022/2026 C++ build tools are required")
    return [
        "-G",
        generators[major],
        "-A",
        "x64",
        "-DCMAKE_GENERATOR_INSTANCE=" + installation["installationPath"],
    ]


def main() -> None:
    """Build/test fixed owned directories; sanitizer and coverage modes never overwrite each other."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    args = parser.parse_args()
    if args.sanitize and args.coverage:
        parser.error("Choose sanitizer or coverage, not both")
    root = Path(__file__).resolve().parents[1]
    name = "native-sanitize" if args.sanitize else "native-build"
    command = [
        build_tool("cmake"),
        "-S",
        str(root),
        "-B",
        str(root / name),
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DPOWER_SANITIZE={'ON' if args.sanitize else 'OFF'}",
        f"-DPOWER_COVERAGE={'ON' if args.coverage else 'OFF'}",
    ]
    if sys.platform == "win32":
        command.extend(windows_generator())
    subprocess.run(command, check=True, timeout=90)
    subprocess.run(
        [
            build_tool("cmake"),
            "--build",
            str(root / name),
            "--config",
            "Release",
            "--parallel",
            "2",
        ],
        check=True,
        timeout=180,
    )
    subprocess.run(
        [
            build_tool("ctest"),
            "--test-dir",
            str(root / name),
            "-C",
            "Release",
            "--output-on-failure",
        ],
        check=True,
        timeout=90,
    )


if __name__ == "__main__":
    main()
