# Validation and evidence

Prepared by Jason Stys. Numerical verification and software tests are not physical validation or flight qualification.

## Executed source checks

Windows x64, Python 3.14.6, Node 24.18.1, MSVC 19.51, CMake 4.4.4:

| Check                                        | Executed result                                                                        |
| -------------------------------------------- | -------------------------------------------------------------------------------------- |
| C++ warning-as-error Release build and CTest | Passed; seven contract groups within one CTest executable                              |
| Python pytest                                | 591 passed; 99.67% combined statement/branch coverage                                  |
| Python Ruff / strict mypy                    | Passed; eight runtime modules type checked                                             |
| TypeScript unit tests / strict build         | 12 passed; production build passed                                                     |
| Playwright                                   | 24 passed across Chromium, Firefox and WebKit                                          |
| Dependency audits                            | npm and hashed Python development lock: no known vulnerabilities reported at execution |
| Numerical benchmark                          | Nine scenario contracts matched declared tolerances                                    |

The benchmark file is generated from real executions, not an invented performance claim. Its example default measured median was about 122 ms with Python allocation tracing enabled; the recorded Python peak was about 1.44 MB. This includes IPC, reference evaluation and tracing, is hardware-specific, and is not native process RSS or a real-time deadline. See [benchmark.json](reports/benchmark.json).

GitHub's [Validation](https://github.com/JasonStys/spacecraft-power-thermal-lab/actions/workflows/validate.yml), [CodeQL](https://github.com/JasonStys/spacecraft-power-thermal-lab/actions/workflows/codeql.yml) and [portable release](https://github.com/JasonStys/spacecraft-power-thermal-lab/actions/workflows/release.yml) runs provide commit-specific cross-platform evidence. Release notes record the exact accepted commit and completed runs. A workflow definition is not itself evidence of a successful run.

## Strategy and independent oracles

- All 324 built-in control combinations use the actual C++ subprocess and independently structured Python implementation. Every output number is compared with relative tolerance `1e-10`, absolute `1e-8`.
- Electrical and thermal ledgers are separately reconstructed in Python and gated at `1e-6 W`. RK4's weighted radiation accounting is a bookkeeping check, not an independent physical model.
- Analytic constant-load battery, adiabatic constant heating, and radiative cooling cases test independent equations; timestep refinement checks numerical convergence where smooth.
- One Hypothesis test executes 100 generated bounded profiles. Native parsing also receives 1,025 malformed envelopes, sizes zero through 1,024. These bounded campaigns are not exhaustive fuzzing or a proof of safety.
- Tests distinguish requested and delivered heater power, intentional science shedding and unmet requested load, charge/discharge saturation, empty/full cells, thermostat and reserve hysteresis, and segment-boundary clipping.
- Schema tests reject duplicate keys, booleans as numbers, enormous integers, NaN/infinity, wrong fields, invalid bands, excess profiles/duration/bytes, bad encoding, native output mismatches and worker failures/timeouts. No fallback fabricates verification.
- HTTP tests exercise Host/Origin/Fetch Metadata checks, traversal/symlink confinement, inert exports, query bounds, absent mutation routes and client disconnects. SQL tests cover identity, immutable records, parameter binding, idempotence, concurrency and the 100-entry limit.
- Browser tests exercise real native-backed replay, policy trade-offs, heater allocation, download formats, opt-in preferences, stale-result removal/retry, hostile labels rendered inert, mobile layout, keyboard access and axe checks. Accessibility checks do not replace user testing.

## Cross-platform gates

Ten Validation jobs cover four OS/Python model combinations, a three-engine browser job, three portable app jobs, Clang AddressSanitizer/UndefinedBehaviorSanitizer, and GCC native line coverage (at least 90%). Python coverage must remain at least 90%. Three separate CodeQL analyses inspect C++, Python and JavaScript/TypeScript; successful analysis does not mean there are no findings, so open alerts are separately reviewed.

Release builds require successful exact-SHA Validation and CodeQL runs. Each of three OS jobs builds the native worker and frozen app, exercises exports/SQL and a real loopback server, and directly uploads its ZIP and checksum to a draft release. These unsigned bundles need independent download/digest verification before publication. No Actions artifacts or caches are uploaded.

## Findings resolved during development

An extreme but syntactically valid JSON integer can raise `OverflowError` when converted implicitly by `math.isfinite`. Bounds are now checked before finiteness conversion in input and native-output guards, with huge-integer regressions. This was an input-validation defect, not a reason to relax bounds.

The restricted local execution environment initially prevented Python temporary writes and Windows SDK registry discovery. A task-owned writable TEMP directory and approved normal compiler execution resolved those environmental restrictions without changing host security settings. Browser and native tests ran with ordinary supported processes, not disabled browser sandboxes.

## Interpretation limits

Physical-model limitations are substantial: invented profiles, one uniform thermal body, ideal sink, fixed heat fractions, no cell chemistry/aging/faults, no real orbit, no continuous-event localization and no measured hardware comparison. End-sample band counts are not continuous exposure durations. Min/max include initial and endpoint samples only. Cross-compiler report hashes are not promised identical: benchmark summaries use `1e-6` absolute / `1e-8` relative tolerances. Audit databases and software versions change; rerun checks for a new release. No test result justifies operational use.
