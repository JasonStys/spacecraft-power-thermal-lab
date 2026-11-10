"""Build and verify versioned portable applications by Jason Stys.

Function: main. Variables: config, source metadata, fixed worker and owned extraction directory.
Only the actual extracted binary is accepted. Exact lines: docs/CODE_INDEX.md. No installer hooks.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

if __package__:
    from .portable_archive import archive_metadata, create_archive, extract_archive
    from .release_contract import ROOT, asset_paths, configuration, require, source_metadata
else:
    from portable_archive import archive_metadata, create_archive, extract_archive
    from release_contract import ROOT, asset_paths, configuration, require, source_metadata


def main() -> int:
    """Build from pinned dependencies, preserve native archive semantics, then exercise extracted UI."""
    parser = argparse.ArgumentParser(
        description="Build and test this platform's portable application"
    )
    parser.add_argument("--output-root", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    config, metadata = configuration(), source_metadata()
    require((ROOT / "web/dist/index.html").is_file(), "Build production web assets first")
    generated = ROOT / ".runtime/package-meta"
    generated.mkdir(parents=True, exist_ok=True)
    identity = generated / "RELEASE.json"
    identity.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    executable_name = config["executable"]
    root = ROOT
    if not (root / "web/dist/index.html").is_file():
        raise SystemExit("Run npm ci and npm run build first")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "SpacecraftPowerThermalLab",
        "--add-data",
        "web/dist:web/dist",
        "--add-binary",
        str(
            root
            / (
                "native-build/Release/power_core.exe"
                if sys.platform == "win32"
                else "native-build/power_core"
            )
        )
        + ":native",
        "--add-data",
        "powerlab/resources:powerlab/resources",
        "--add-data",
        "LICENSE:licenses/project",
        "--add-data",
        "licenses/PYTHON.txt:licenses/python",
        "--add-data",
        "docs/THIRD_PARTY.md:docs",
        "--add-data",
        "node_modules/vite/LICENSE.md:licenses/vite",
        "launcher.py",
    ]
    if sys.platform == "linux":
        for notice in (
            "/usr/share/doc/libstdc++6/copyright",
            "/usr/share/doc/libgcc-s1/copyright",
            "/usr/share/common-licenses/GPL-3",
        ):
            source = Path(notice)
            if not source.is_file():
                raise SystemExit("Expected Ubuntu/Debian GCC runtime notices")
            destination = "licenses/compiler-runtime/" + source.parent.name
            command[command.index("launcher.py") : command.index("launcher.py")] = [
                "--add-data",
                str(source) + ":" + destination,
            ]
    distribution_info = distribution("pyinstaller")
    notices = [
        distribution_info.locate_file(path)
        for path in distribution_info.files or []
        if str(path).endswith("licenses/COPYING.txt")
    ]
    if len(notices) != 1:
        raise SystemExit("Expected the locked PyInstaller distribution license")
    command[command.index("launcher.py") : command.index("launcher.py")] = [
        "--add-data",
        str(notices[0]) + ":licenses/pyinstaller",
    ]
    command[command.index("launcher.py") : command.index("launcher.py")] = [
        "--add-data",
        str(identity) + ":powerlab/resources",
    ]
    subprocess.run(command, cwd=ROOT, check=True, timeout=600)
    bundle = ROOT / "dist" / executable_name
    shutil.copyfile(identity, bundle / "RELEASE.json")
    archive, checksum = asset_paths(metadata)
    archive, checksum = (
        args.output_root.resolve() / archive.name,
        args.output_root.resolve() / checksum.name,
    )
    archive.parent.mkdir(parents=True, exist_ok=True)
    require(not checksum.exists(), "Checksum destination already exists")
    create_archive(bundle, archive)
    require(
        archive_metadata(archive, executable_name) == metadata, "Created archive identity mismatch"
    )
    with tempfile.TemporaryDirectory(prefix="flight-extracted-") as temporary:
        extracted = extract_archive(archive, Path(temporary) / "unpacked", executable_name)
        executable = extracted / (executable_name + (".exe" if sys.platform == "win32" else ""))
        subprocess.run(
            [sys.executable, str(ROOT / "tools/smoke_app.py"), str(executable)],
            cwd=temporary,
            check=True,
            timeout=120,
        )
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Extracted portable application passed: {archive.name} SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
