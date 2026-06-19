# Test Plan — <Project Name>

> Stage 2 deliverable, due end of **W5 (June 12, 2026)**.
> Lives at `docs/test_plan.md` on branch `<namespace>/stage2` in your greenfield repo. **No tag — the branch name is the indicator** (do not tag).
> This document plus your TDD-first scaffolding (failing tests with informative messages) are the two halves of Stage 2.
> Length target: 2-3 pages + the traceability table (which can run longer).

---

## 0. Metadata

| Field              | Value                                           |
| ------------------ | ----------------------------------------------- |
| Project            | Deadliner                                       |
| Linked PRD version | `docs/PRD.md` v1                                |
| Linked design doc  | `docs/design_doc.md` v1                         |
| Branch             | `team-typed-aura/stage2`                        |
| Test framework     | `pytest`                                        |
| CI workflow        | `.github/workflows/test.yml` — [Link to CI Run] |

---

## 1. Test strategy (1 paragraph)

We test the core fetchers (`MoodleFetcher`, `ClassroomFetcher`) and the domain logic (`DeadlineFormatter`, CLI) via isolated unit and integration tests to ensure they handle edge cases like timezone cutoffs and auth failures. We explicitly do not test the internals of the `requests` library, the Google API client, or the standard `argparse` module. The suite is shipped TDD-first (red), meaning all components are currently stubs that fail loudly with informative messages.

---

## 2. Test inventory

A flat list of every test file and every test case. Use the AAA pattern: name communicates _Arrange / Act / Assert_ intent.

### Test naming convention

`test_<unit>_<scenario>_<expected>` — e.g., `test_importer_empty_file_returns_empty_list`.

### Inventory

| #   | Test file                         | Test name                                                   | Type        | Status |
| --- | --------------------------------- | ----------------------------------------------------------- | ----------- | ------ |
| 1   | `tests/test_moodle_fetcher.py`    | `test_fetch_moodle_valid_token_returns_assignments`         | integration | red    |
| 2   | `tests/test_moodle_fetcher.py`    | `test_fetch_moodle_empty_calendar_returns_empty_list`       | integration | red    |
| 3   | `tests/test_classroom_fetcher.py` | `test_fetch_classroom_valid_oauth_returns_assignments`      | integration | red    |
| 4   | `tests/test_classroom_fetcher.py` | `test_fetch_classroom_no_active_courses_returns_empty_list` | integration | red    |
| 5   | `TBD (teammate)`                  | `TBD (teammate)`                                            | unit        | red    |

> Stage 2 awards **5 points** for "Test plan covers P0 including invalid input and empty-argument edge cases." Edge-case coverage = empty, one-element, max-realistic-size, malformed input, missing required arg.

---

## 3. Traceability matrix (P0 requirement → test)

Every P0 user story from `PRD.md §3.1` must map to **at least one** test in §2. **This is the rubric.**

| PRD requirement (ID)                         | Tests covering it (numbers from §2) |
| -------------------------------------------- | ----------------------------------- |
| US-01 (connect Moodle and Classroom & empty) | 1, 2, 3, 4                          |
| US-02 (list deadlines sorted ascending)      | TBD (teammate)                      |
| US-03 (distinguish 00:00 from 23:59)         | TBD (teammate)                      |
| US-04 (exit non-zero on connector failure)   | TBD (teammate)                      |

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

## 5. What I am explicitly _not_ testing (and why)

| Skipped surface                  | Reason                                |
| -------------------------------- | ------------------------------------- |
| Stdlib `csv` module internals    | Owned by Python stdlib team, not me   |
| argparse error messages verbatim | Brittle to library upgrades           |
| Performance for >1M rows         | Out of NFR scope; P0 targets 10k rows |

---

## 6. CI / runner setup

- **Test runner**: `pytest` invoked by `pytest -v tests/`.
- **CI workflow**: `.github/workflows/test.yml`.
- **Green-CI evidence**: The CI run on GitHub Actions correctly executes the suite and shows all P0 tests failing with informative messages (red CI).
- **Pre-commit hook**: Not configured yet (mandatory by W7).

---

## 7. Manual test cases (Part C)

### US-01: Happy Path (Data exists)

| Field               | Description                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **Title**           | US-01 — Fetch combined list from Moodle and Classroom                                                  |
| **Preconditions**   | Valid tokens in `~/.deadliner/credentials.json`. Both platforms have at least 1 active assignment.     |
| **Steps**           | 1. Run `deadliner fetch` in the terminal.                                                              |
| **Expected Result** | Stdout prints a combined list of deadlines. Each line has the tag `[moodle]` or `[classroom]`.         |
| **Actual Result**   | `[TBD by execution]`                                                                                   |

### US-01: Edge Case (Empty Account)

| Field               | Description                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **Title**           | US-01 — Handle empty accounts without crashing                                                         |
| **Preconditions**   | Valid tokens present. Moodle account has 0 active assignments.                                         |
| **Steps**           | 1. Run `deadliner fetch` in the terminal.                                                              |
| **Expected Result** | Exit code 0; stdout explicitly shows `0 upcoming deadlines found`; no traceback or errors are thrown.  |
| **Actual Result**   | `[TBD by execution]`                                                                                   |

---

## 8. Sign-off

Solo: "Reviewed alone, <date>."
Team: each member confirms they reviewed and ran the test scaffolding locally.
