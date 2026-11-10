# Documentation refresh — 2026-11-09

By Jason Stys.

This documentation-only edition describes source `5f4f3ae0c6cf5e3f04bb0c3fc4ee5bbc94266d96`. It does not change application behavior, accounts, private data, installers or published releases.

## Published editions and completed review

| File                                                 | Bytes | SHA-256                                                            | Reviewed scope                                                                                                                      |
| ---------------------------------------------------- | ----: | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| [project-guide.docx](project-guide.docx)             | 72652 | `362bc893cb3dd0f503c5c5d7c799e962200d0489f87e7940e2d1d9bc6c22f059` | 5 pages, each viewed individually                                                                                                   |
| [validation-review.docx](validation-review.docx)     | 42062 | `5c531f1d73cf21c572bf4f47a1fcb98391c673263ab12ba83e1c50ebbcbf10c5` | 3 pages, each viewed individually                                                                                                   |
| [validation-evidence.xlsx](validation-evidence.xlsx) |  7396 | `38af8d179e953d9a3aafab890230a6178ed6b247667ecb9cc91705317a076c5c` | Both tab previews; two actual Excel Tables/autoFilters; four formulas; failure-change/restore recalculation and zero formula errors |

Word review checked plain black titles, readable pagination, whole table rows, source references, practical limits and absence of clipping or overflow. Render receipts were matched to the current DOCX digest before approval. Workbook review inspected both tab previews and actual exported Table/autoFilter elements; recalculated success/failure summaries were compared independently with workflow metadata. Static previews do not draw Excel dropdown arrows; the exported workbook contains the actual filters.

## Evidence and change boundary

- Functional baseline: `5f4f3ae0c6cf5e3f04bb0c3fc4ee5bbc94266d96`.
- Workflow observation: `2026-11-10T05:25:40.628667+00:00`; exact run URLs and source identities remain in [publications.json](publications.json).
- Local document-package validation verifies exact copied bytes, Office ZIP integrity, approved page/tab identities and internal documentation links. Repository-specific documentation and source-policy commands are run separately and recorded in the integration handoff.
- Source/index metadata is regenerated using the repository’s existing tools. Existing privacy, security, coverage and workflow gates are retained.
- PR and later main workflows must pass independently. This record does not claim future or unrun integration CI success.

## Interpretation

The Word files document the cited source; dated source reports retain their original execution scope. A passing workflow is distinct from completed analysis with zero findings, and neither establishes production suitability. The Excel source inventory is not a per-test execution report. Checksums identify exact bytes, not a signature or publisher attestation.

Use the [handbook](../handbook.md) to choose usage, design, security and test documentation. Keep editable Markdown and reviewed editions together; do not replace historical measurements with undated claims.

## Local integration validation

The complete Python suite passed 691 tests at 99.71% combined statement/branch
package coverage, retaining the original 90% floor and warning policy. Eight real
Office ZIP regressions are included: only the three named editions are decoded,
with bounded bytes/members and strict UTF-8 XML/relationships; their text remains
visible to the existing privacy scan. Unknown binaries, malformed ZIPs, absent roots
and oversized members fail. Package and CLI imports remain explicit.

Ruff, exact generated code/file inventories, 12 TypeScript unit tests, strict
TypeScript/Vite production build, formatting and exact approved Office/source/link
validation passed. The current integration changes documentation and its validator,
not simulation behavior, stores or published portable releases. Original cross-OS,
sanitizer and browser gates still run in hosted CI; this local pass does not claim
those unrun integration results or a new installation/release.
