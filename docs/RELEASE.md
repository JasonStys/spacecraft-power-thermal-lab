# Release and operations runbook

Maintained by Jason Stys. Scope: an unsigned local educational application, not a production/flight service.

## Before shipping

1. Inspect current Actions artifact usage and the available billing quota; distinguish artifacts, accumulated billing and caches. Report storage concerns to the owner. Never delete runs, artifacts or caches without fresh approval and verified private backups.
2. Review the exact source diff, physical claims, schema bounds, provenance, licenses, dependency locks and secrets exclusions. Update formatted docs and regenerate `python tools/verify_repo.py --write`; rerun without `--write`.
3. Run the README checks and real browser QA. Read failure logs to distinguish source defects from execution/toolchain failures; add a regression for a source defect. Do not suppress warnings or weaken physical/coverage gates to create a green badge.
4. Push the reviewed commit. Require all ten Validation jobs and all three CodeQL analyses on that exact SHA. Separately inspect open CodeQL alerts. Account limitations or queued jobs are not successful results.

## Build and publish

Dispatch **Portable release** with a fresh semantic tag, for example `v1.0.0`, against the reviewed `main` commit. Its preparation job checks completed successful exact-SHA Validation/CodeQL runs and creates a draft only; three platform jobs independently build/test/package their app. No Actions artifact or cache upload is used. ZIP/checksum pairs are directly uploaded to this draft.

Download all six assets to a new task-owned directory. Verify each `.sha256` against its ZIP and, where available, GitHub's asset SHA-256 digest. Inspect ZIP contents for the whole folder, assets, native worker and license notices; never execute an old archived Actions artifact. Execute only the newly built, reviewed Windows release locally. Test a real export, a custom input, optional SQL history and browser interaction. Keep the report and test evidence private if it contains local paths.

Document source SHA, completed workflow links, test counts/coverage, sanitizer and audit results, checksum verification, actual downloaded-app checks and known limits in release notes. Publish the existing draft only after these checks pass. Confirm public release assets and that the tag/main/source gates refer to the intended commit. Do not claim code signing, notarization, universal mobile support or hardware validation.

## Local operation and privacy

Only `127.0.0.1` is bound; no remote accounts, cookies, AI service or telemetry. Exports/history are explicit opt-in writes by the CLI. Browser preferences are opt-in local storage. SQL history is unencrypted, capped and immutable at the application level; OS users with file access can still read/change files. Closing a tab does not stop its server. Ctrl+C its console; stop only the process launched for this app, never a broad port/process kill.

During development, previews use a task-owned process/port and production assets. Check readiness, inspect actual desktop and mobile behavior, capture an unmodified application screenshot, and stop owned preview processes after QA. Do not leave development listeners running as a substitute for an installed app.

## Rollback and maintenance

If a published build fails digest, gate, or reproducibility checks, stop distribution and explain the affected version; preserve evidence and do not overwrite published assets silently. Build a corrected new version through the same gates. Users can remove an extracted portable folder after closing the process; exports and databases are separate user-owned files and must not be deleted automatically. No background updater, scheduled collection or automatic cleanup exists.

Changes to physics, integration or thresholds require independent oracle tests and updated limitations, not merely refreshed benchmark values. Dependency changes require lock regeneration, license review, audits and all platform checks. Storage checks never authorize account-wide cleanup by themselves.
