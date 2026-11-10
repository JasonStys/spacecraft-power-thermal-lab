# Portable release refresh validation — 2026-11-09

By Jason Stys. Version 1.1.0 prepares per-load service interruption review, right-censored outage intervals and separate intentional science shedding.

## Recorded checks

On Windows/Python 3.14.6, 683 Python tests passed with99.71% combined coverage (unchanged90% gate), 12 TypeScript tests and27 actual source Chromium/Firefox/WebKit journeys passed. Native C++ contract 1 passed, Ruff/strict mypy/build passed, and all9 numerical benchmark contracts remain unchanged. The packaged new UI checks independently integrate 6 W requested minus 3.2 W served over600 seconds, verify component deficits reconcile to total Wh, and compare actual downloaded JSON with the frozen API.

The actual Windows archive was inspected and extracted into a fresh temporary directory. Its executable ran from an unrelated working directory, preserved every previous native smoke contract, served only its owned loopback URL, matched package/version/instance identity, delivered actual compiled assets and completed the new real Chromium workflow/export. Local archive SHA-256: `e14ecf53b3f01b1739a1d2cf98536d092efd0389f3fadc27b8f6d4d435493959`. This development archive honestly records dirty-source metadata; it is local acceptance evidence rather than a published clean-source release.

The original seventy release/archive/runtime tests use independent GitHub metadata fixtures and actual small archive bytes. They reject wrong source/version/repository, running/failed/incomplete/ambiguous workflow histories, existing draft/tag/public release, asset/checksum/metadata mismatch, link/path escape and corrupt frozen identity. Release guards remain active under optimized Python. No GitHub writes occur in these tests. Existing coverage, native/oracle, security and browser gates remain unchanged.

## Reproduce and limits

The follow-up product-identity audit found the same-named CMake project still declared 1.0.0. It now declares 1.1.0, and the active packaging/release configuration guard rejects a differing CMake version. A negative source fixture independently exercises the mismatch; the native kernel algorithm and evidence schema remain unchanged.

Use exact development locks and target native toolchains. Run the repository's full coverage suite, deterministic benchmark, strict lint/types/index/format checks, TypeScript tests/build and three-engine source browser suite, then `python tools/package_app.py`. The last command launches the real extracted application and its new feature in Chromium; it needs Node/Playwright only as build-time acceptance tools. Ordinary users need neither Python nor Node.

Fictional single-body/battery model with independent Python numerical checks; neither agreement nor energy closure establishes real spacecraft safety, battery validation or operational power control.

Local native acceptance covers Windows only. Linux/macOS executable, links, ABI and UI still require real native CI. These unsigned portable folders are not installers or clean-machine installation proof. Native tests bypass the default OS browser opener, whose frozen POSIX inherited-library behavior remains a manual desktop check. No accounts, previous releases or user histories are changed. No push, dispatch, tag or release mutation was performed by this local work. The coordinator must review clean exact-source main checks, all three native jobs and all six uploaded assets/checksum digests before publishing.

## Authenticated draft lookup correction

The hosted application/UI checks passed before upload exposed an API-contract error: GitHub's releases-by-tag endpoint returns published releases and can return 404 for an untagged draft. Preparation and upload now use a complete authenticated release listing (100 entries per page, at most three pages), require a unique exact tag and reread its numeric release ID. They validate list/detail identity and same-repository API/upload/assets URLs; upload additionally requires the exact source and non-prerelease draft state. A full cap, duplicated or swapped identity, lost access, malformed metadata, 404 or network error cannot authorize absence or a write.

All19 independent real-shape API contract tests pass in the complete recorded suite. Existing archive/checksum/source/collision/non-clobber guards remain active; no application acceptance, coverage, security or native-OS job was removed or skipped. The previous actual extracted Windows workflow and separate three-engine source journeys remain recorded above; this follow-up changes release metadata acquisition, not the application feature or its numerical kernel. No live upload, draft mutation, push or workflow dispatch was performed by this local correction.
