# Release, operation and rollback

By Jason Stys. Portable bundles are unsigned, software-only and not flight qualified.

## Build and preflight

1. Use reviewed source, supported Python/Node and compiler; install development lockfiles with hashes. Build native tests and production web assets.
2. Run the complete lint/type/unit/property/HTTP/browser/golden replay gates. Confirm CI's ASan/UBSan, coverage, security analysis, audits and all3OS bundle smoke jobs pass on the exact commit. Check account Actions storage; no automatic deletion or cleanup is authorized by these tools.
3. Install the locked development graph and Chromium (`npx playwright install --with-deps chromium`), then run `python tools/package_app.py` on the target OS. The fixed native dependencies when required, built assets and application resources and project/CPython/PyInstaller notices are bundled. Windows uses ZIP; POSIX uses tar.gz to preserve internal relative links and execute bits. Version, OS and CPU appear in the archive name and `RELEASE.json`.
4. The archive is inspected and extracted into a fresh temporary directory before its executable is launched from an unrelated working directory. Acceptance checks existing native CLI/export contracts, non-overwrite behavior, the current practical workflow JSON, instance/version/source identity, actual compiled JS/CSS bytes and a genuine Chromium UI/export journey. No source backend or existing user server supplies a passing response.
5. `python tools/smoke_app.py path/to/extracted/SpacecraftPowerThermalLab` repeats the owned journey using the adjacent release manifest. This development test needs Node/Playwright; ordinary app users do not. Only its child process/browser/temp files are stopped or removed. For repeat local builds, `--output-root .runtime/another-owned-build` selects a new archive destination; existing archives/checksums are not overwritten.

## GitHub release workflow

Dispatch **Portable release** from main with the exact version in Python/npm/runtime source metadata (currently 1.1.0). The clean checkout, workflow SHA and current main must agree. Every returned exact-source Validation/CodeQL run must be completed/successful, with exactly one main-push run per workflow; incomplete histories, failed/running runs and duplicate pushes require explicit review. An older success cannot hide an unfinished check.

Preparation requires both tag and release version to be absent. Only the Git tag-ref lookup treats an explicit HTTP404 as absence; release absence requires a complete authenticated listing. Network/authentication errors do not authorize creation. A new draft is created at the exact SHA. Existing drafts, public releases and tags are not retargeted or reused. A failed draft may remain for review; use a reviewed fresh version rather than silently replacing its source.

Three OS jobs independently build and exercise the actual extracted application, including its Chromium feature journey. Upload rechecks draft status, target SHA, tag absence, canonical software version, archive manifest and exact SHA-256. Only that platform's versioned archive/checksum pair is sent, without clobbering existing assets. Direct draft transport needs job-level contents-write permission; checkout does not persist credentials, and GH_TOKEN is exposed as an environment variable only to preparation/upload steps. Dependencies are locked and actions pinned. No Actions artifact/cache uploads are added.

Before publishing: ensure the exact-source checks and all three extracted-native jobs passed. Require exactly six assets: Windows ZIP/SHA256, Linux tar.gz/SHA256 and macOS tar.gz/SHA256, each with its actual CPU label. Match uploaded API digests to the checksum bytes; download and re-exercise the matching local OS bundle. Record workflow/source/release links. The coordinator publishes only after this review; no helper automatically publishes. Release assets are separate from Actions storage. Published releases/assets and user histories are preserved.

## Operate

Extract the entire OS/CPU-matching bundle, then launch its executable with `serve` (the launcher defaults to serve when no arguments). On POSIX, use a native tar extractor and a filesystem supporting relative symlinks. The app opens a fresh loopback URL in the default browser. `serve --no-browser` prints the URL without opening a tab. The process stays in the console; Ctrl+C stops it. There is no installation service, background task, cloud login, real telemetry source, device connection or OS security change. Keep the folder together; moving only the executable breaks resource discovery. Linux/macOS compatibility follows the build's OS ABI and CPU, not every historical OS release.

The [PyInstaller distribution guidance](https://pyinstaller.org/en/latest/common-issues-and-pitfalls.html#requirements-imposed-by-symbolic-links-in-frozen-application) explains why POSIX links must survive packaging. Archive extraction uses explicit member/content budgets, one application root and Python's data filter. The local instance marker is a test identity check, not an account or authentication system.

## Rollback

If reports diverge, the app crashes, a trust problem is suspected or checks regress: stop the local app, preserve synthetic evidence, mark the affected release unsuitable in its notes, and use a previously reviewed release/source version. Do not mutate or delete user history. Use a new database/export destination for a schema change; version data explicitly. There is no real spacecraft/production control system to roll back, no remote user migration and no destructive uninstall step. Delete/extract folders only under the user's normal file-management decisions.

The native automation uses `--no-browser` and tests its owned URL directly in Chromium. Automatic opening of the user's default desktop browser is not established by that proof; frozen POSIX external launchers can inherit bundled library search settings. If the OS opener fails, copy the printed loopback URL into the browser. No environment or OS security settings are changed by this release.

## Draft API identity

GitHub's published-only release-by-tag endpoint is unsuitable for an untagged draft. Both preparation collision checks and upload lookup use complete authenticated pages (100 releases/page, at most three pages), then a unique exact tag and a numeric-ID reread. A full cap, repeated ID/tag, changed list/detail identity, foreign hypermedia, missing access or malformed response fails closed. Upload still checks exact source, draft/non-prerelease state, absent tag, archive metadata, SHA-256 and collisions before its existing no-clobber transport. New public source metadata must pass all unchanged workflows before a fresh release attempt.
