# docs/CONTRIBUTIONS.md

## C.1 — Contribution block

| Team Member | Area of Ownership & Contribution |
|---|---|
| **surovytsky1vadym-1** | **PRD & Multi-source Aggregation:** Authored the target persona and core motivation for aggregating disjointed platforms (Google Classroom integration). Drove the PRD's P0 definition around fetching and filtering. |
| **ofedkevych** | **CLI Business Logic & NFRs:** Contributed the "midnight cutoff" business logic and strict timezone enforcement requirements. Defined the stateless CLI boundaries and local JSON credential management in the Design Doc. |
| **vkatsel** | **Calendar Integration Architecture:** Designed the `CalendarGateway` architecture and formulated the P1 requirements for idempotent synchronization with Google Calendar. Validated the stateless approach against caching anti-patterns. |

Each member's initial drafts (W2–W4) formed the basis of this consolidated Stage 1 release.

**Signatures:**
- This reflects my actual contribution — surovytsky1vadym-1, 2026-06-11
- This reflects my actual contribution — ofedkevych, 2026-06-11
- This reflects my actual contribution — vkatsel, 2026-06-11

---

## C.2 — Peer-review response table

Below is an exhaustive list of peer review comments (W2–W4), grouped by team member. 

### Reviews for ofedkevych's branches

| Peer comment (link or quote) | Verdict | Reason |
|---|---|---|
| W4 PR [#137](https://github.com/CS460-SEP-2026/greenfield/pull/137): @milenayer "In user stories there is a strict dependency on the current system time... pass 'now' and 'local_tz' explicitly" | Applied (fully) | In the final `DeadlineFormatter` (Section 3), we explicitly inject `now` and `local_tz` to ensure the function is pure and testable. |
| W4 PR [#137](https://github.com/CS460-SEP-2026/greenfield/pull/137): @dburdak "DeadlineFormatter as a class vs standalone pure function... dropping the class wrapper" | Applied (fully) | We removed `Manager/Helper/Formatter` classes and kept formatting as pure functions or strict contracts. |
| W4 PR [#137](https://github.com/CS460-SEP-2026/greenfield/pull/137): @milenayer "Criterion for AuthError is too general... test should check specific message." | Applied (fully) | Added the `fail loudly` requirement with specific error messages in the NFRs. |
| W4 PR [#137](https://github.com/CS460-SEP-2026/greenfield/pull/137): @dburdak "Expected Result / Actual Result discipline" | Applied (fully) | Enforced a strict contract for tests in §6 (Test Seam Map). |
| W3 PR [#95](https://github.com/CS460-SEP-2026/greenfield/pull/95): @ArseniiKlimenko "You explicitly ban an offline cache for P0... However, US-05 states previously fetched list is NOT wiped... resolve this contradiction" | Applied (fully) | The contradiction was resolved during consolidation: we completely abandoned the cache (stateless fetch) and removed this requirement. |
| W3 PR [#95](https://github.com/CS460-SEP-2026/greenfield/pull/95): @ArseniiKlimenko "what if a student has two 'Midterm Exam'... tiebreak must include the course name as well" | Applied (fully) | Updated the sorting logic, adding guaranteed determinism by sorting by `course_name` first (US-02). |
| W3 PR [#95](https://github.com/CS460-SEP-2026/greenfield/pull/95): @akoshelieva "Handling missing course shortnames... downgrade to p1" | Applied (fully) | Downgraded the priority of this specific feature, simplifying the baseline output. |
| W3 PR [#95](https://github.com/CS460-SEP-2026/greenfield/pull/95): @akoshelieva "NFR section... define what 'local timezone' means" | Applied (fully) | Added strict verification for timezone conversion in the NFR section. |
| W3 PR [#95](https://github.com/CS460-SEP-2026/greenfield/pull/95): @akoshelieva "Discard rationale says session auth is bad... focus entirely on security risk" | Applied (fully) | Explicitly stated in the PRD that using tokens (OAuth/REST) is a security requirement. |
| W2 PR [#58](https://github.com/CS460-SEP-2026/greenfield/pull/58): @saveliikozlov "'I get an alert' is under-specified... Pick a channel and write it into the Then." | Rejected (Consolidation) | During consolidation, we completely rejected notifications (Telegram/Push) as over-engineering (documented in §3.4). |

### Reviews for surovytsky1vadym-1's branches

| Peer comment (link or quote) | Verdict | Reason |
|---|---|---|
| W4 PR [#125](https://github.com/CS460-SEP-2026/greenfield/pull/125): @ysobko "Plugin registry seems useful only if third-party... it would add a lot of complexity" | Applied (fully) | We rejected complex plugin registries; instead, we used strictly defined `MoodleFetcher` and `ClassroomFetcher` entities in the final design. |
| W4 PR [#125](https://github.com/CS460-SEP-2026/greenfield/pull/125): @ysobko "what should happen when two deadlines have exactly the same due date." | Applied (fully) | Resolved via an alphabetical tie-breaker. |
| W3 PR [#83](https://github.com/CS460-SEP-2026/greenfield/pull/83): @saveliikozlov "the pattern only checks that a date appears somewhere... require the date to be the last thing on the line" | Applied (fully) | Output formatting and regex requirements now enforce a strict pattern (e.g., the `[midnight cutoff]` label at the end). |
| W3 PR [#83](https://github.com/CS460-SEP-2026/greenfield/pull/83): @nvytska "add an acceptance criterion for the case where a valid Moodle course has no active assignments (0 assignments found)" | Applied (fully) | Added explicit requirements for handling empty lists (exit code 0, but with a clear message) to distinguish it from authorization errors. |

### Reviews for vkatsel's branches

| Peer comment (link or quote) | Verdict | Reason |
|---|---|---|
| W4 PR [#110](https://github.com/CS460-SEP-2026/greenfield/pull/110): @ysobko "S-01 Then step says system establishes secure connection... make it more testable (e.g. returning specific number of Assignments)" | Applied (fully) | In `design_doc.md`, the `fetch_moodle` function contracts strictly return `list[Assignment]` for testability. |
| W4 PR [#110](https://github.com/CS460-SEP-2026/greenfield/pull/110): @ysobko "wondering how system will identify which Google Calendar event should be updated." | Applied (fully) | In the final design, we defined event mapping by saving `source_moodle_id` in the `extendedProperties` of GCal events. |
| W3 PR [#76](https://github.com/CS460-SEP-2026/greenfield/pull/76): @kdeneshchuk "S-08 silent failure (network error returns empty list and deletes all GCal events) - how do you suppose to handle such critical bug?" | Applied (fully) | Because this is an extremely critical risk, we moved the deletion feature (Delete Cleanup) to the P2/low-priority list. |
| W3 PR [#76](https://github.com/CS460-SEP-2026/greenfield/pull/76): @ysobko "This AC only says that request is sent to GCal, but it doesn't require checking actual payload fields..." | Applied (fully) | Test contracts now require validation of fields (timezone, title) BEFORE the payload is dispatched. |
| W3 PR [#76](https://github.com/CS460-SEP-2026/greenfield/pull/76): @ysobko "The update story mentions gcal.patch()... should require stable source assignment ID instead of matching only by title." | Applied (fully) | Again, resolved by introducing `source_moodle_id` to guarantee 100% idempotency. |
| W3 PR [#76](https://github.com/CS460-SEP-2026/greenfield/pull/76): @nvytska "S-02 AC should also verify that the authenticated account is the expected one..." | Applied (fully) | We included OAuth token validation as a security NFR. |
| W3 PR [#76](https://github.com/CS460-SEP-2026/greenfield/pull/76): @nvytska "Open Question needs clarification because it mixes two ideas... caching and stateless execution" | Applied (fully) | During consolidation, we entirely discarded the caching idea in favor of stateless execution, removing the conflict. |
| W2 PR [#46](https://github.com/CS460-SEP-2026/greenfield/pull/46): @kdeneshchuk "S-05 has words like reliable and reusable... move them to NFR with concrete numbers" | Applied (fully) | All subjective characteristics were moved to NFR §4 as measurable metrics (e.g., 'under 5 seconds'). |
| W2 PR [#46](https://github.com/CS460-SEP-2026/greenfield/pull/46): @ysobko "Main feature test should assert key fields" | Applied (fully) | Applied to the API contracts. |

---

## C.1 (Stage 2) — Contribution block

This stage turned the Stage 1 P0 contracts into a TDD-first test suite (red, with informative messages) plus the test plan and CI. Ownership spans the test plan and the suite, with distinct stories per member.

| Team Member | Stage 2 Ownership & Contribution |
|---|---|
| **vkatsel** | **Infrastructure + US-01.** Configured `pytest`, authored the CI workflow `.github/workflows/test.yml`, wrote `test_plan.md` §0 (metadata) and §1 (strategy). Created `tests/test_moodle_fetcher.py` and `tests/test_classroom_fetcher.py` with the US-01 happy-path and empty-list tests, the matching manual test, and the §3 traceability rows for US-01. |
| **ofedkevych** | **US-02 + US-03.** Created `tests/test_formatter.py` (8 tests): midnight-cutoff vs 23:59 (US-03), course-shortname prefix and empty-shortname fallback, ascending sort, course+title tie-break, empty-list and single-item edges (US-02). Added the US-02/US-03 manual cases (§7), Inventory rows 5–12 (§2), traceability mappings (§3), and the §4/§5 edge-case and out-of-scope notes. |
| **surovytsky1vadym-1** | **US-04 + Stage-2 administration.** Added the US-04 auth-failure tests to `tests/test_moodle_fetcher.py` and `tests/test_classroom_fetcher.py` (invalid/revoked token raises `AuthError`; auth failure must not return an empty list; missing OAuth `access_token` treated as auth failure). Added the US-04 manual cases (§7), Inventory rows 13–16 (§2), the US-04 traceability mapping (§3), and the US-04 edge cases (§4). Refreshed this Stage-2 contribution block, collected §8 sign-offs, and verified the CI run is red via `AssertionError` (missing behaviour) rather than a collector crash. |

**Stage 2 signatures:**
- This reflects my actual contribution — vkatsel, 2026-06-23
- This reflects my actual contribution — ofedkevych, 2026-06-23
- This reflects my actual contribution — surovytsky1vadym-1, 2026-06-23

## C.1 Stage 3 Contributions

| Member | Contribution details |
|---|---|
| **vkatsel** | **Component 1 (Moodle Fetcher) & Tooling Config:** Implemented the `fetch_moodle` logic utilizing the `requests` library and parsing the Moodle REST API response. Configured `responses`-based HTTP mocks to ensure US-01 and US-04 tests pass. Set up the strict `pre-push` git hook and the native `make ci` pipeline using `run_ci.sh` wrapper. |
| **surovytsky1vadym-1** | **Component 2 (Classroom Fetcher):** Implemented `fetch_classroom` against the real Google Classroom REST API (`courses` + `courseWork` endpoints) using `requests`, mirroring the Moodle fetcher's style. Rewrote `test_classroom_fetcher.py` to import from `src` and mock both endpoints with `responses`, replacing the old magic-string-token stubs. Also added the missing `requirements.txt` and fixed `.github/workflows/test.yml` (added the `stage3` trigger branch, switched it to run `make ci`) so CI actually runs and has the dependencies it needs. |
| **ofedkevych** | **Component 3 (Formatter, CLI & Config):** Implemented `src/deadliner/formatter.py` — `format_assignment` (UTC→local conversion **before** the midnight-cutoff classification, course-shortname prefix with `[Course ID: …]` fallback, `Xd Yh` countdown) and `sort_assignments` (ascending by `due_utc`, tiebreak by `course_shortname` then `title`, returns a new list). Rewired `tests/test_formatter.py` from Stage 2 stubs to import from `src` — all 8 tests green with bodies unchanged. Implemented `src/deadliner/cli.py` (`fetch` subcommand via stdlib `argparse`; env-var/config-file credentials; `AuthError`/`ConnectionError` → stderr + non-zero exit). Added `tests/test_cli.py` (3 `monkeypatch` integration tests for the failure paths). Reviewed and cleaned `pyproject.toml` (pytest + ruff config). Wrote the Component 3 section of `docs/devtest_notes.md`. |

**Stage 3 signatures:**
- This reflects my actual contribution — vkatsel, 2026-07-01
- This reflects my actual contribution — surovytsky1vadym-1, 2026-07-04
- This reflects my actual contribution — ofedkevych, 2026-07-05
