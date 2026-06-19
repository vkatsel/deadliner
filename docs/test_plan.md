# Test Plan — <Project Name>

> Stage 2 deliverable, due end of **W5 (June 12, 2026)**.
> Lives at `docs/test_plan.md` on branch `<namespace>/stage2` in your greenfield repo. **No tag — the branch name is the indicator** (do not tag).
> This document plus your TDD-first scaffolding (failing tests with informative messages) are the two halves of Stage 2.
> Length target: 2-3 pages + the traceability table (which can run longer).

---

## 0. Metadata

| Field | Value |
|---|---|
| Project | <Name> |
| Linked PRD version | `docs/PRD.md` v<n> |
| Linked design doc | `docs/design_doc.md` v<n> |
| Branch | `<namespace>/stage2` (no tag — branch name is the indicator) |
| Test framework | <pytest / JUnit 5 / vitest / XCTest / GoogleTest> |
| CI workflow | `.github/workflows/<name>.yml` — link to the first CI run (red is expected at Stage 2) |

---

## 1. Test strategy (1 paragraph)

Two sentences on what you test and what you do **not** test. Examples:
- "I test the `Importer` and `Reporter` via unit tests; the CLI via subprocess integration tests; I do not test argparse itself or the stdlib `csv` module."
- "Stage 2 ships failing tests by design — all P0 tests fail with informative messages. They turn green incrementally in W6-W8."

---

## 2. Test inventory

A flat list of every test file and every test case. Use the AAA pattern: name communicates *Arrange / Act / Assert* intent.

### Test naming convention

`test_<unit>_<scenario>_<expected>` — e.g., `test_importer_empty_file_returns_empty_list`.

### Inventory

| # | Test file | Test name | Type (unit / integ / e2e) | Status at Stage-2 (red / green) |
|---|---|---|---|---|
| 1 | `tests/test_importer.py` | `test_importer_one_row_returns_one_txn` | unit | red |
| 2 | `tests/test_importer.py` | `test_importer_empty_file_returns_empty_list` | unit | red |
| 3 | `tests/test_importer.py` | `test_importer_malformed_row_raises_typed_error` | unit | red |
| 4 | `tests/test_importer.py` | `test_importer_utf8_bom_handled` | unit | red |
| 5 | `tests/test_reporter.py` | `test_reporter_by_category_sums_amounts` | unit | red |
| 6 | `tests/test_cli.py` | `test_cli_import_then_report_end_to_end` | integration | red |

> Stage 2 awards **5 points** for "Test plan covers P0 including invalid input and empty-argument edge cases." Edge-case coverage = empty, one-element, max-realistic-size, malformed input, missing required arg.

---

## 3. Traceability matrix (P0 requirement → test)

Every P0 user story from `PRD.md §3.1` must map to **at least one** test in §2. **This is the rubric.**

| PRD requirement (ID) | Tests covering it (numbers from §2) |
|---|---|
| US-P0-1 (user imports CSV → sees total) | 1, 6 |
| US-P0-2 (empty CSV → no error, empty report) | 2 |
| US-P0-3 (malformed CSV → typed error) | 3 |
| US-P0-4 (UTF-8 BOM tolerated) | 4 |
| US-P0-5 (report grouped by category) | 5 |

> If a P0 story has zero tests, either add a test or downgrade the requirement to P1. Don't leave it unmapped.

---

## 4. Edge cases I deliberately included

A short list of the "boring but important" cases. Mine these from your Mini #1 / Mini #2 anti-pattern observations.

- Empty input file
- Single-row input
- Input with only the header row
- File with trailing newline / no trailing newline
- File with UTF-8 BOM (planted bug surface in Mini #1)
- File with European date format (`31/12/2026`)
- File with quoted commas inside fields
- Missing file path argument

---

## 5. What I am explicitly *not* testing (and why)

| Skipped surface | Reason |
|---|---|
| Stdlib `csv` module internals | Owned by Python stdlib team, not me |
| argparse error messages verbatim | Brittle to library upgrades |
| Performance for >1M rows | Out of NFR scope; P0 targets 10k rows |

---

## 6. CI / runner setup

- **Test runner**: `<pytest>` invoked by `<make test>` / `<npm test>` / etc.
- **CI workflow**: link to `.github/workflows/<name>.yml`.
- **Green-CI evidence**: link to the workflow run where all *scaffolding* tests are present and fail with informative messages (red CI is expected at Stage 2 — see §7).
- **Pre-commit hook** (optional this week, mandatory by W7): runs lint + test before commit.

---

## 7. "Tests fail cleanly with informative messages" — Stage-2 rubric clarification

At Stage 2, all P0 tests are expected to be **red**. Grading checks that:
- Each red test prints a clear failure message — *not* `AssertionError: assert False`.
- The failure message names the missing behaviour (e.g., `AssertionError: Importer.import not implemented yet`).
- A `pytest -v` run lists every test by name without crashing the collector.

This is the discipline of TDD: write the test red, with a message that tells future-you (or your team-mate) what implementation is missing.

---

## 8. Sign-off

Solo: "Reviewed alone, <date>."
Team: each member confirms they reviewed and ran the test scaffolding locally.
