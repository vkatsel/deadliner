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
| 5  | tests/test_formatter.py | test_format_assignment_midnight_utc_kyiv_shows_midnight_cutoff           | unit | red |
| 6  | tests/test_formatter.py | test_format_assignment_end_of_day_does_not_show_midnight_cutoff          | unit | red |
| 7  | tests/test_formatter.py | test_format_assignment_includes_course_shortname_as_prefix               | unit | red |
| 8  | tests/test_formatter.py | test_format_assignment_empty_course_shortname_shows_fallback             | unit | red |
| 9  | tests/test_formatter.py | test_sort_assignments_out_of_order_returns_ascending                     | unit | red |
| 10 | tests/test_formatter.py | test_sort_assignments_identical_due_dates_tiebreak_by_course_then_title  | unit | red |
| 11 | tests/test_formatter.py | test_sort_assignments_empty_list_returns_empty                           | unit | red |
| 12 | tests/test_formatter.py | test_sort_assignments_single_item_returns_unchanged                      | unit | red |
| 13 | `tests/test_moodle_fetcher.py`    | `test_fetch_moodle_invalid_token_raises_auth_error`            | integration | red |
| 14 | `tests/test_moodle_fetcher.py`    | `test_fetch_moodle_invalid_token_does_not_return_empty_list`   | integration | red |
| 15 | `tests/test_classroom_fetcher.py` | `test_fetch_classroom_revoked_oauth_raises_auth_error`         | integration | red |
| 16 | `tests/test_classroom_fetcher.py` | `test_fetch_classroom_missing_access_token_raises_auth_error`  | integration | red |

> Stage 2 awards **5 points** for "Test plan covers P0 including invalid input and empty-argument edge cases." Edge-case coverage = empty, one-element, max-realistic-size, malformed input, missing required arg.

---

## 3. Traceability matrix (P0 requirement → test)

Every P0 user story from `PRD.md §3.1` must map to **at least one** test in §2. **This is the rubric.**

| PRD requirement (ID)                         | Tests covering it (numbers from §2) |
| -------------------------------------------- | ----------------------------------- |
| US-01 (connect Moodle and Classroom & empty) | 1, 2, 3, 4                          |
| US-02 (list deadlines sorted ascending)    | 9, 10, 11, 12 |
| US-03 (distinguish 00:00 from 23:59)       | 5, 6, 7, 8    |
| US-04 (exit non-zero on connector failure) | 13, 14, 15, 16 |

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
- Deadline at exactly 00:00 local time (midnight) must be labeled — not just "close to midnight"
- Deadline at 23:59 local time must NOT receive the midnight cutoff label
- Empty course shortname renders as `[Course ID: <id>]`, never as `[]`
- Two deadlines with identical `due_utc` — sort order is deterministic across repeated calls
- Empty assignment list passed to sort — returns empty list without raising
- Single-item list passed to sort — returns the same item unchanged
- Invalid / revoked auth token — raises `AuthError`, never returns an empty list (Mini #1 silent-200 anti-pattern)
- OAuth credentials dict missing its `access_token` field — treated as an auth failure, not as "no courses"

---

## 5. What I am explicitly _not_ testing (and why)

| Skipped surface                           | Reason                                                       |
| ------------------------------------------| ------------------------------------------------------------ |
| Stdlib `csv` module internals             | Owned by Python stdlib team, not me                          |
| argparse error messages verbatim          | Brittle to library upgrades                                  |
| Performance for >1M rows                  | Out of NFR scope; P0 targets 10k rows                        |
| `zoneinfo` / `ZoneInfo` DST transitions   | Stdlib correctness; we inject fixed offsets in tests         |
| Actual Moodle API timezone field values   | Integration concern; unit tests use hardcoded UTC datetimes  |
| Sort stability for >1000 items            | Out of P0 NFR scope; Python's sort is stable by spec         |

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
### US-02: Happy Path (Sorted list)

| Field              | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Title**          | US-02 — Deadlines appear sorted by due date ascending                      |
| **Preconditions**  | Valid Moodle token. At least 3 upcoming assignments across 2 courses, added to Moodle in non-chronological order. |
| **Steps**          | 1. Run `deadliner fetch` in the terminal.                                  |
| **Expected Result**| Output lines are in ascending due-date order. The earliest deadline appears first. Each line includes the course short name. |
| **Actual Result**  | [TBD by execution]                                                          |

### US-02: Edge Case (Identical timestamps)

| Field              | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Title**          | US-02 — Two deadlines with the same due time appear in consistent order    |
| **Preconditions**  | Two assignments in different courses set to the exact same due time.       |
| **Steps**          | 1. Run `deadliner fetch` twice in a row.                                   |
| **Expected Result**| Both runs produce the same order; the assignment from the alphabetically earlier course appears first. |
| **Actual Result**  | [TBD by execution]                                                          |

### US-03: Happy Path (Midnight cutoff labeled)

| Field              | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Title**          | US-03 — A 00:00 local-time deadline is labeled "midnight cutoff"            |
| **Preconditions**  | A Moodle assignment is set to due at 21:00 UTC (= 00:00 Europe/Kyiv). System timezone is Europe/Kyiv. |
| **Steps**          | 1. Run `deadliner fetch`.                                                   |
| **Expected Result**| The deadline line shows `00:00` and contains the text `midnight cutoff`.    |
| **Actual Result**  | [TBD by execution]                                                          |

### US-03: Edge Case (23:59 not mislabeled)

| Field              | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Title**          | US-03 — A 23:59 local-time deadline is NOT labeled midnight cutoff          |
| **Preconditions**  | A Moodle assignment due at 20:59 UTC (= 23:59 Europe/Kyiv).                 |
| **Steps**          | 1. Run `deadliner fetch`.                                                   |
| **Expected Result**| The line shows `23:59`. The text "midnight cutoff" does NOT appear.         |
| **Actual Result**  | [TBD by execution]                                                          |

### US-04: Happy Path (Connector failure is loud)

| Field               | Description                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **Title**           | US-04 — An invalid Moodle token causes a loud non-zero exit                                             |
| **Preconditions**   | `~/.deadliner/credentials.json` contains an invalid or revoked Moodle token. Classroom token may be valid. |
| **Steps**           | 1. Run `deadliner fetch` in the terminal. 2. Inspect stderr and the shell exit code (`echo $?`).        |
| **Expected Result** | Exit code is non-zero; stderr contains `auth error`; no `[moodle]` lines are printed. The failure is never swallowed into an empty-but-successful run. |
| **Actual Result**   | `[TBD by execution]`                                                                                   |

### US-04: Edge Case (Auth failure not masked as empty)

| Field               | Description                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| **Title**           | US-04 — A revoked token must not look like a healthy-but-empty account                                  |
| **Preconditions**   | Moodle token is revoked (would 401). The account otherwise has zero assignments anyway.                 |
| **Steps**           | 1. Run `deadliner fetch`. 2. Compare behaviour against the US-01 empty-account case.                    |
| **Expected Result** | Exit is non-zero with an `auth error` on stderr — distinct from the US-01 empty case, which exits 0 with `0 upcoming deadlines found`. The two outcomes are never conflated (Mini #1 anti-pattern). |
| **Actual Result**   | `[TBD by execution]`                                                                                   |
---

## 8. Sign-off
- Reviewed and ran scaffolding locally — ofedkevych, 2026-06-23
- Reviewed and ran scaffolding locally — vkatsel, 2026-06-23
- Reviewed and ran scaffolding locally — surovytsky1vadym-1, 2026-06-23
