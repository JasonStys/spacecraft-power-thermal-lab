# HELIO user guide

Created by Jason Stys. This is an offline educational experiment, not a spacecraft operations tool.

## First experiment

Launch the extracted portable application, or run `python -m powerlab serve` after the source build. Leave its console open. The app opens only a loopback address in your normal browser. Closing the tab does not stop the service; Ctrl+C in its console does.

1. Select **Illumination cycle**. Leave the 40 Wh battery, Always requested policy, 5 second integration step and heater enabled. Reserve-aware is an optional comparison, not the default.
2. Read the verification gates before interpreting the charts. Both implementations must agree and both energy ledgers must close. An error removes stale results instead of showing an apparently current answer.
3. Move the interval slider, use previous/next, or jump to the end. Power values describe the selected interval; battery energy and temperature describe its end. Lines connect samples; they do not establish continuous extrema or exact switching times.
4. Inspect the priority table. Housekeeping receives available bus power first, then heater, then science. A heater request does not imply that all requested heater power was available.
5. Pin a result, change one control, and compare. A pin lives only in this page's memory, not in a database or account.

## Useful comparisons

| Experiment                          | What to inspect                                                                                                                           |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Extended eclipse, policy 0 versus 1 | Reserve protection reduces delivered science. Intentional science shedding and unmet requested energy are different totals; inspect both. |
| Heater contention                   | A requested heater receives partial power after housekeeping; science receives none in the initial interval.                              |
| Full battery                        | Charge stops at capacity; surplus solar is spilled.                                                                                       |
| Empty battery                       | Discharge cannot create energy; service depends on present solar.                                                                         |
| Isolated cooling, step 10 then 1    | Compare against the analytic cooling law and refinement tests; this does not validate spacecraft hardware.                                |
| Hot soak / cold start               | Temperature bands are illustrative thresholds, not certified safety limits.                                                               |

Changing battery size also changes initial chemical energy at the same initial state of charge. These are prescribed illumination profiles, not predicted orbits. Temperature plots can switch to Celsius without changing SI evidence. Preference storage is opt-in; disabling it removes saved controls from browser local storage.

## Download and customize

JSON contains the complete report and provenance; CSV contains dimensioned interval samples; HTML is an escaped, static report; input JSON contains the complete editable configuration and segments. See [API](API.md) for exact bounds and units. Browser controls deliberately expose only finite experiments, not arbitrary file execution or uploads.

For a custom experiment, download input JSON, edit a copy, then run the CLI:

```powershell
python -m powerlab export --input my-case.json --step 1 --policy 1 --format json --output new-report.json
```

The imported `config.battery_wh` is authoritative; `settings.battery` is a recorded unused preset for imports. Read `input` for actual physical parameters. Unknown fields, duplicate keys, non-finite values, excessive durations and oversized files fail closed. The CLI never overwrites an existing export. Its optional `--history private.sqlite3` records up to 100 distinct verified reports in an unencrypted local database; duplicate reports are idempotent. Keep private evidence outside the repository and back it up yourself.

## Troubleshooting and help

- Missing native worker: build it with `python tools/build_native.py`. There is no silent reference-only fallback.
- Missing assets: run `npm ci` and `npm run build` before source launch.
- Verification or numerical-domain error: preserve a small synthetic input and the error. Do not discard the gate or expand physical claims to force a result.
- Port in use: omit `--port` for an ephemeral port; do not stop unrelated processes.
- Portable launch blocked: do not bypass OS protection. Verify the ZIP checksum and use reviewed source if unsigned applications are prohibited.
- Privacy: no login, remote telemetry, advertisements, AI provider, cloud upload or device access is present. Local users with access to your OS files can read local evidence.

Contact [Jason Stys](https://github.com/JasonStys), or open a [project issue](https://github.com/JasonStys/spacecraft-power-thermal-lab/issues) with synthetic, non-sensitive information. Review [MODEL](MODEL.md) before using any result.
