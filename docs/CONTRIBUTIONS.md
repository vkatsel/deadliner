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
| W1 PR [#27](https://github.com/CS460-SEP-2026/greenfield/pull/27): @achaika01 "slight disconnect between the high levels of student anxiety described and the current P0 scope." | Applied (fully) | Bridged the gap by explicitly targeting the exact anxiety triggers: we added the 00:00 vs 23:59 (midnight cutoff) distinction and multi-platform aggregation to the P0 scope. |
| W1 PR [#27](https://github.com/CS460-SEP-2026/greenfield/pull/27): @OBudiak "I don't quite see the proposed solution yet. Could you clarify the main approach... add some minimal comments to the empty code files" | Applied (fully) | The architecture was fully specified in the W4 design phase (CLI aggregator + GCal Gateway) and we stubbed the empty files with strict API surface contracts in the `design_doc.md`. |

### Reviews for surovytsky1vadym-1's branches

| Peer comment (link or quote) | Verdict | Reason |
|---|---|---|
| W4 PR [#125](https://github.com/CS460-SEP-2026/greenfield/pull/125): @ysobko "Plugin registry seems useful only if third-party... it would add a lot of complexity" | Applied (fully) | We rejected complex plugin registries; instead, we used strictly defined `MoodleFetcher` and `ClassroomFetcher` entities in the final design. |
| W4 PR [#125](https://github.com/CS460-SEP-2026/greenfield/pull/125): @ysobko "what should happen when two deadlines have exactly the same due date." | Applied (fully) | Resolved via an alphabetical tie-breaker. |
| W3 PR [#83](https://github.com/CS460-SEP-2026/greenfield/pull/83): @saveliikozlov "the pattern only checks that a date appears somewhere... require the date to be the last thing on the line" | Applied (fully) | Output formatting and regex requirements now enforce a strict pattern (e.g., the `[midnight cutoff]` label at the end). |
| W3 PR [#83](https://github.com/CS460-SEP-2026/greenfield/pull/83): @nvytska "add an acceptance criterion for the case where a valid Moodle course has no active assignments (0 assignments found)" | Applied (fully) | Added explicit requirements for handling empty lists (exit code 0, but with a clear message) to distinguish it from authorization errors. |
| W1 PR [#29](https://github.com/CS460-SEP-2026/greenfield/pull/29): @ddanyliuk18 "what happens to deadlines that have already passed? Does the tool show them, hide them, or mark them differently? ...worth defining explicitly" | Applied (fully) | We added an explicit P1 story (US-06) to filter out past deadlines so the list is not polluted with last week's submissions. |
| W1 PR [#29](https://github.com/CS460-SEP-2026/greenfield/pull/29): @ivasylenko1 "you can easily export all moodle deadlines to google calendar with a few clicks" | Applied (partially) | Acknowledged that Moodle has an iCal export, but it doesn't aggregate Classroom, and the native iCal sync is notoriously delayed. We updated our core motivation to focus on *aggregating multiple* disjointed platforms (Moodle + Classroom). |

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
| W1 PR [#28](https://github.com/CS460-SEP-2026/greenfield/pull/28): @TretenichenkoDaria "moodle actually already has a built in feature to export an ical link that syncs directly with google calendar... also it would be better to have more motivation" | Applied (partially) | We expanded the motivation to focus specifically on the aggregation of Moodle AND Google Classroom, which native Moodle iCal cannot solve natively. |
