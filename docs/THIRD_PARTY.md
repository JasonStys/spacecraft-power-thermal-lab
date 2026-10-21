# Notices and scientific references

Maintained by Jason Stys. Project-authored source is MIT licensed; third-party components retain their own terms. A project license does not replace bundled dependency notices.

## Portable application contents

| Component                                   | Notice location in the extracted bundle                                                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Project source                              | `_internal/licenses/project/LICENSE`                                                                                           |
| CPython                                     | `_internal/licenses/python/PYTHON.txt` (actual interpreter notice retained in source `licenses/`)                              |
| PyInstaller bootloader/runtime hooks        | `_internal/licenses/pyinstaller/COPYING.txt`, copied from the locked distribution                                              |
| Vite-generated browser runtime              | `_internal/licenses/vite/LICENSE.md`, copied from the actual locked Vite package, including its third-party notices            |
| Linux GCC runtime libraries, when collected | `_internal/licenses/compiler-runtime/` contains actual Ubuntu/Debian libstdc++/libgcc package copyright notices and GPL-3 text |

PyInstaller distributes its bootloader under GPL with an exception for applications built with it; see the actual COPYING notice rather than interpreting this summary as legal advice. GCC runtime notices include the GCC Runtime Library Exception and underlying license terms. Linux packaging fails if expected distribution notices are absent. Windows native model uses the static MSVC runtime; macOS uses the platform C++ runtime. OS frameworks and libraries remain subject to their respective terms. Bundles are console applications, not an Electron distribution.

Development-only dependencies (pytest, Hypothesis, Ruff, mypy, coverage tools, audit/build tools, TypeScript, Vitest, Playwright, axe and formatters) are pinned in the hash/integrity locks. Their packages are not indiscriminately redistributed in the portable application. `npm ci` and the hash-checked Python lock establish build dependencies; license and security review is still required when changing those locks.

## Scientific context, not imported datasets

- [NASA Small Spacecraft Technology: Power Subsystems](https://www.nasa.gov/smallsat-institute/sst-soa/power-subsystems/) provides context for generation, storage and power distribution. This lab invents all sizing and illumination profiles; it does not implement a NASA design.
- [NASA Small Spacecraft Technology: Thermal Control](https://www.nasa.gov/smallsat-institute/sst-soa/thermal-control/) describes spacecraft heat-balance context. This repository implements its own deliberately simplified absorbed/generated/stored/radiated energy model.
- [NIST/CODATA Stefan–Boltzmann constant](https://physics.nist.gov/cgi-bin/cuu/Value?sigma%7Csearch_for=stefan+boltzmann) gives `5.670374419… × 10^-8 W m^-2 K^-4`. The implementation uses the finite decimal `5.670374419e-8`, not an uncertainty-qualified measurement or complete exact decimal expansion.

No NASA/NIST software, page prose, image or operational dataset is incorporated. References are attribution/context, not endorsement, certification or physical validation. All screenshots show this application's synthetic cases. No credentials, personal data, mission telemetry, device addresses or account exports belong in this repository.
