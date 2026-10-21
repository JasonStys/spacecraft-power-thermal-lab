# Strict input and interface contracts

Author: Jason Stys. Version 1 is a lab-specific synthetic profile format, not an industry telemetry or command protocol.

## JSON profile

Start with [examples/illumination.json](../examples/illumination.json). Exact top-level fields are `schema` (integer 1), `name` (1–48 lowercase alphanumeric/hyphen characters, first alphanumeric), `config` and `segments`. Unknown/missing fields, duplicate JSON keys, booleans in numeric fields, strings, nonfinite/huge numbers, malformed UTF-8, excessive nesting and files larger than 32 KiB are rejected. The reader requests at most 32 KiB plus one sentinel. Segment order is meaningful and is never sorted away.

`config` must contain every field below and no others. Quantities are actual finite JSON numbers; inclusive input bounds are numerical guardrails, **not a validated physical envelope**.

| Field                                        | Units        | Bounds                             |
| -------------------------------------------- | ------------ | ---------------------------------- |
| `solar_area_m2`                              | m²           | 0–1                                |
| `solar_efficiency`                           | fraction     | 0–0.5                              |
| `battery_wh`                                 | chemical Wh  | 1–200                              |
| `initial_soc`                                | fraction     | 0–1                                |
| `charge_efficiency`, `discharge_efficiency`  | fraction     | 0.1–1                              |
| `charge_limit_w`, `discharge_limit_w`        | bus W        | 0–200                              |
| `heat_capacity_j_k`                          | J/K          | 1,000–10,000                       |
| `radiator_area_m2`, `projected_area_m2`      | m²           | 0–1                                |
| `emissivity`, `absorptivity`                 | fraction     | 0–1                                |
| `sink_k`                                     | K            | 0–50                               |
| `external_heat_w`, `base_load_w`, `heater_w` | W            | 0–100                              |
| `heater_on_k`                                | K            | 180–350                            |
| `heater_off_k`                               | K            | 180–360; strictly greater than on  |
| `reserve_off`, `reserve_on`                  | SOC fraction | 0–1; on strictly greater than off  |
| `initial_temp_k`                             | K            | 180–360                            |
| `min_temp_k`                                 | K            | 180–350                            |
| `max_temp_k`                                 | K            | 180–400; strictly greater than min |

`segments` is a JSON list of 1–32 exact objects: `duration_s` (integer 1–3,600), `solar_flux_w_m2` (0–2,000 W/m²), `payload_w` (0–150 W). Total duration may not exceed 3,600 seconds. Zero flux/load is valid. A final clipped interval may be shorter than the selected step.

## Controls and worker

Browser settings are exactly `scenario`, `battery` (20/40/80 Wh), `policy` (0 always-requested, 1 reserve-aware), `step` (1/5/10 seconds), and `heater` (0 disabled, 1 hysteresis). Imported files preserve their own capacity: `settings.battery` is recorded but not applied; the actual parameter is `input.config.battery_wh`. Policy/step/heater apply to imports. Built-in cases apply the battery preset before execution.

The fixed `power_core` binary receives at most 32 KiB stdin: `POWER1 step policy heater`, then a `P` row with 24 configuration numbers in the declared C++/Python field order, then 1–32 `S duration flux payload` rows. It accepts no caller-selected path, command-line configuration, URL or device. Invalid input/numerical failure exits 2 with a constant diagnostic and no partial successful stdout. This internal format is not a public stable interchange protocol; use JSON through the CLI.

Python enforces a five-second worker deadline and rejects output larger than 8 MiB, more than 3,600 rows, missing/extra numeric fields and nonfinite values. Captured output is size-checked after process completion, not through a hostile-child streaming quota. The bounded trusted worker plus full independent numerical comparison is the primary output guarantee.

## Read-only HTTP

The server binds only IPv4 `127.0.0.1`, default ephemeral port. No account, upload/import, filesystem-write, hardware, shell or remote-fetch endpoint exists.

| Route                                                                   | Result                                         |
| ----------------------------------------------------------------------- | ---------------------------------------------- |
| `/`, confined `/assets/*`                                               | Built production UI assets                     |
| `/api/health`                                                           | Fixed local mode/status JSON                   |
| `/api/catalog`                                                          | Finite scenarios/settings/defaults             |
| `/api/run?scenario=day-night-cycle&battery=40&policy=0&step=5&heater=1` | Independently verified full report             |
| `/api/report?...&format=json`                                           | Fixed-name JSON, HTML, CSV or `input` download |

Exact Host (loopback plus listener port), same Origin when supplied, and Fetch Metadata restrictions block cross-site/rebinding use. CORS is not granted. Request targets >1 KiB, >8 query fields, duplicate/unknown fields and unsupported controls fail. Unknown assets/path traversal/symlink escapes are not served. Success and error responses carry restrictive CSP, no-store, frame, referrer, content-sniffing and permissions headers. Errors are generic; native/reference failure is not turned into fake data. Disconnected response peers are abandoned without a second write.

## Evidence and storage

Reports contain normalized full input, selected controls, source/method provenance, limitations, complete interval samples and totals. All powers are W, times seconds, body temperature K and battery energy chemical Wh; the UI's Celsius display does not mutate evidence. Sample fields are fixed in `native/core.hpp` and `powerlab/reference.py`; definition locations are in [CODE_INDEX](CODE_INDEX.md). The [model guide](MODEL.md) defines interval order, accounting and flags.

`id` is SHA-256 of sorted-key, indented ASCII canonical JSON excluding its own id, with a final newline and no NaN/infinity. Values are rounded to nine decimal places before hashing; different compilers can produce different quantized identities. Hashes are content identities, **not signatures**. Machine paths, wall-clock timing, usernames and secrets are absent.

JSON/HTML retain the full report. HTML escapes all evidence and has no scripts/external resources. CSV contains selected dimensioned numeric interval fields only, not all provenance/parameters; obtain JSON too when needed. `input` contains the strict reusable profile. CLI destinations are create-only and never overwritten.

`--history` verifies report identity and uses parameterized SQL, immediate transactions, idempotent same-key insertion, update/delete refusal triggers and a 100-distinct-report cap without pruning. These are application safeguards, not protection from a filesystem owner who can replace an unencrypted SQLite file. History is never exposed by HTTP and is not a saved-state resume mechanism.
