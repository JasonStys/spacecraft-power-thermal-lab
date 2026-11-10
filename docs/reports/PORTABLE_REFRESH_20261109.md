# Portable release refresh validation — 2026-11-09

By Jason Stys. Version 1.1.0 prepares per-load service interruption review, right-censored outage intervals and separate intentional science shedding.

## Recorded checks

Windows/Python3.14.6:663 Python tests passed with99.71% combined coverage (unchanged90% gate),12 TypeScript tests and27 actual source Chromium/Firefox/WebKit journeys passed. Native C++ contract1 passed, Ruff/strict mypy/build passed, and all9 numerical benchmark contracts remain unchanged. The packaged new UI checks independently integrate6W requested minus3.2W served over600seconds, verify component deficits reconcile to total Wh, and compare actual downloaded JSON with the frozen API.

The actual Windows archive was inspected and extracted into a fresh temporary directory. Its executable ran from an unrelated working directory, preserved every previous native smoke contract, served only its owned loopback URL, matched package/version/instance identity, delivered actual compiled assets and completed the new real Chromium workflow/export. Local archive SHA-256: `e14ecf53b3f01b1739a1d2cf98536d092efd0389f3fadc27b8f6d4d435493959`. This development archive honestly records dirty-source metadata; it is local acceptance evidence rather than a published clean-source release.

Seventy new release/archive/runtime tests use independent GitHub metadata fixtures and actual small archive bytes. They reject wrong source/version/repository, running/failed/incomplete/ambiguous workflow histories, existing draft/tag/public release, asset/checksum/metadata mismatch, link/path escape and corrupt frozen identity. Release guards remain active under optimized Python. No GitHub writes occur in these tests. Existing coverage, native/oracle, security and browser gates remain unchanged.

## Reproduce and limits

Use exact development locks and target native toolchains. Run the repository's full coverage suite, deterministic benchmark, strict lint/types/index/format checks, TypeScript tests/build and three-engine source browser suite, then `python tools/package_app.py`. The last command launches the real extracted application and its new feature in Chromium; it needs Node/Playwright only as build-time acceptance tools. Ordinary users need neither Python nor Node.

Fictional single-body/battery model with independent Python numerical checks; neither agreement nor energy closure establishes real spacecraft safety, battery validation or operational power control.

Local native acceptance covers Windows only. Linux/macOS executable, links, ABI and UI still require real native CI. These unsigned portable folders are not installers or clean-machine installation proof. Native tests bypass the default OS browser opener, whose frozen POSIX inherited-library behavior remains a manual desktop check. No accounts, previous releases or user histories are changed. No push, dispatch, tag or release mutation was performed by this local work. The coordinator must review clean exact-source main checks, all three native jobs and all six uploaded assets/checksum digests before publishing.
