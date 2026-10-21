# Architecture and trade-offs

Author: Jason Stys. This repository asks how power allocation and heat accounting interact in a **bounded fictional** system. It does not connect to real spacecraft or electrical equipment.

## Components and boundaries

```text
Finite browser selectors -> protected read-only Python loopback API
Explicit CLI local JSON -> strict SI profile validation
                      -> fixed C++ executable, bounded stdin envelope
                      -> independent Python state/flow replay
                      -> compare every numerical sample
                      -> independently audit both energy ledgers
                      -> canonical evidence / static reports / optional CLI SQL history
```

Inputs cannot choose a worker, URL, shell command, device or network address. Native code performs no network/file operations: stdin and stdout only. Full parsing and numerical work complete before successful output is emitted. Worker failure, reference disagreement, nonfinite data or a failed ledger withholds evidence. The reference is never a fallback.

## Decisions

| Decision                                 | Benefit                                                                                    | Cost / boundary                                                                     |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Standard-library C++20 numerical worker  | Portable typed bounded hot loop, explicit numerical phases, native test/sanitizer tooling  | Source builds need a compiler; no general thermal solver or electrochemistry        |
| Independent Python dictionary/flow model | Every state/flow has a separately structured check, not just summary comparison            | Additional CPU/IPC cost; shared specification mistakes remain possible              |
| Fixed-step RK4 with boundary clipping    | Understandable integration and reproducible finite work; exact imposed-profile transitions | Sample-held control decisions and averaged saturation; no event-localized switching |
| One body plus one chemical-energy store  | Clear units and separately checkable electrical/thermal budgets                            | No spatial temperatures, cell voltage, aging, radiation damage or real geometry     |
| TypeScript/browser SVG UI                | Responsive portable interface, typed contracts, no external scripts/fonts                  | Local desktop service, not public hosting or mobile installation                    |
| Opt-in immutable SQLite evidence         | Explicit persistence, content identity and safe SQL parameters                             | Unencrypted local data; no multiuser isolation, cloud sync or saved-state resume    |
| Tolerance-based metric contracts         | Allows justified floating-point differences across compilers                               | Report hashes identify quantized content, not universal cross-platform identities   |

Each stage has a narrow error contract; no report embeds machine paths or timestamps. Parameters and imposed inputs travel with the data. JSON is the full evidence record; CSV intentionally exposes dimensioned interval samples, not every metadata field. Static HTML is escaped JSON with no executable content.

## Numerical work and complexity

Let S≤32 be imposed segments and N≤3,600 be integration intervals (minimum 1 second, maximum 3,600 seconds). Segment boundaries clip steps, so each loop advances at least one second. Per interval there is a constant number of allocation operations, hysteresis decisions and four radiation evaluations: **O(S+N) time and O(N) stored sample memory**, with O(1) evolving model state. Full reference comparison, energy audits and report serialization are also linear in sample count. The browser plots every sample, so chart/replay redraw is O(N), not constant time. A 100-entry history bounds entry count, not a precisely measured SQLite byte footprint.

The runtime benchmark measures real native IPC plus Python verification/report/tracing overhead on a fixed default workload. Its traced Python peak is not native RSS, full process memory or a hard real-time bound. Numerical error is evaluated separately against analytic cases; speed does not establish physical accuracy.

## Reliability and growth

Browser requests supersede/abort old fetches, stale evidence is hidden on failure, and canceled sockets do not trigger a second error write. Server requests are read-only and bounded, but the development HTTP service is not a hostile multiuser resource-quota system; concurrent local clients can consume CPU/threads. CLI paths are explicit user decisions and never passed through HTTP.

Future work would require independently validated spacecraft geometry/thermal nodes, actual battery/PMAD models, mission-specific environments, uncertainty/calibration data and event-resolving integration. Public deployment would additionally require authentication, TLS, quotas, tenant isolation and a different service architecture. None is implied by successful lab tests.
