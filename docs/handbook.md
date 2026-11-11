# Spacecraft Power Thermal Lab handbook

By Jason Stys.

The released 1.1.0 HELIO portable app includes per-load service review: inspect requested and delivered energy, grouped shortfalls with censored boundaries, and deliberately shed science demand separately.

The C++ numerical model and independent Python energy/reference checks remain intact. The actual extracted UI is tested against an independent 6 W minus 3.2 W over 600 seconds energy calculation, component-to-total reconciliation and an exact JSON download. Product-version identity and preserved native notices make the practical analysis available in a reviewable portable bundle.

## Read the documentation

The [illustrated Windows guide](reports/windows-application-guide.docx) adds actual
installed-app screenshots, a worked scenario, source excerpts and dated acceptance.
Its [review manifest](reports/windows-application-guide.json) identifies the exact
reviewed bytes. Earlier Office editions below retain their historical baselines.

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions, and the workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)
- [releases/v1.1.0](releases/v1.1.0.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [MODEL](MODEL.md)

### Security and validation

- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`5f4f3ae0c6cf5e3f04bb0c3fc4ee5bbc94266d96`](https://github.com/JasonStys/spacecraft-power-thermal-lab/tree/5f4f3ae0c6cf5e3f04bb0c3fc4ee5bbc94266d96). The observed functional workflow baseline is `5f4f3ae0c6cf5e3f04bb0c3fc4ee5bbc94266d96`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_REFRESH_20261109.md)
- [Current Actions](https://github.com/JasonStys/spacecraft-power-thermal-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Fictional single-body/battery model; numerical agreement and balanced energy do not validate real batteries or establish spacecraft safety.
- No live hardware, power control or operational thermal assurance.
- Unsigned desktop portable folders, not system installers or clean-machine proof. Three-OS extracted-native checks drive an owned URL; default OS browser opening remains manual.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
