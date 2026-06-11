# docs/PRD.md — Deadliner, v1

## §0 Metadata
- **Author(s):** team-typed-aura (ofedkevych, surovytsky1vadym-1, vkatsel)
- **Version:** v1
- **Repo URL:** [greenfield monorepo]
- **Branch:** `team-typed-aura/stage1`
- **Linked Design Doc:** `docs/design_doc.md`

## §1 Problem & motivation
Pablo Garcia is a second-year CS student with ADHD and anxiety. He lives on learning portals — assignments, quizzes, submissions. He has deadlines on Moodle, a group project on Google Classroom, and a lab on a department portal. His coping strategy is notifications — if his phone doesn't buzz, the deadline doesn't exist. Moodle notifies him one hour before, Classroom sometimes doesn't notify him at all. Twice a month he finds out about a deadline at 23:00 when it's due at 00:00 (because he never knows if "due Tuesday" means midnight or end-of-day). He's tried a spreadsheet; it rots. He's tried Google Calendar; manual entry is a sustained administrative task that doesn't happen when you have ADHD. The deadlines are all there perfectly organized, just never in the same place at the same time. Nobody is aggregating them for him. That's what Deadliner does.

## §2 Existing solutions & gap
1. **Spreadsheets (Google Sheets v2024)**: Flexible but requires manual entry and maintenance; rots after two weeks.
2. **Native Moodle/Classroom Notifications (vCurrent)**: Fragmented across platforms, different timings (e.g., 1 hour before vs none), easy to miss.
3. **Manual Google Calendar entries (vCurrent)**: Accurate but requires sustained administrative effort to copy-paste tasks, which users with ADHD fail to maintain.

**Gap:** There is no single, automated tool that aggregates deadlines from multiple disjointed learning platforms (Moodle, Classroom) into one unified timeline and exports them directly into a personal calendar without manual intervention.

## §3 Scope decisions

### §3.1 P0 stories (Core Value)

| ID | Role | Want | So that | Acceptance Criteria (G/W/T) | Priority Justification |
|---|---|---|---|---|---|
| **US-01** | student | connect my Moodle and Classroom instances | the tool can fetch my deadlines without logging in every time | **Given** valid tokens in config, **When** I run `deadliner fetch`, **Then** stdout contains a sorted list of deadlines with `[moodle]` and `[classroom]` labels and exit code is 0. | Essential for multi-source data ingestion. |
| **US-02** | student | list deadlines sorted by due date ascending | the most urgent thing is always at the top | **Given** fetched deadlines from both platforms, **When** I run `deadliner fetch`, **Then** the output is sorted ascending by due date (verified by parsing each output line's date). | "Sorted list" is the core promise. |
| **US-03** | student | distinguish 00:00 from 23:59 deadlines | I never mistake a midnight cutoff for end-of-day | **Given** a deadline stored as `21:00:00Z` and system timezone `Europe/Kyiv` (UTC+3), **When** I run `deadliner fetch`, **Then** output shows `00:00` labeled `midnight cutoff`. | Solves a primary pain point mentioned in motivation. |
| **US-04** | student | exit with non-zero and print an error when a connector fails | I notice data is missing instead of trusting a silently incomplete list | **Given** an invalid Moodle token in config, **When** I run `deadliner fetch`, **Then** exit code is non-zero, stderr contains "auth error", and no `[moodle]` lines are printed. | Prevents silent failures of partial lists. |

### §3.2 P1 stories
- **US-05: Sync to Google Calendar:** As a student, I want to sync the aggregated list to Google Calendar, so that I have the deadlines on my phone natively. (Justification: A massive UX boost over CLI text, fulfilling the ultimate product vision).
- **US-06: Filter out past deadlines:** As a student, I want to filter out past deadlines by default, so I don't wade through missed tasks. (Justification: Meaningful usability improvement, but basic flat list works without it).

### §3.3 P2 stories
- **US-07: Delete Cleanup:** As a student, I want canceled assignments cleared from Google Calendar, so my calendar is accurate. (Justification: Deletion is a risky operation; must be rock-solid before implementation, definitely post-P0).

### §3.4 NOT in scope
- **Telegram / push notifications:** Explicitly cut from P0. Adding a notification layer means OAuth for a bot, webhook setup, and a persistent background process — that's a separate product.
- **Background Daemon Execution:** We drop the idea of a background syncing tool (cron jobs). Running a CLI tool as a background process with foreground error handling leads to invisible failures.
- **SQLite Database:** A local relational database is over-engineered for MVP. Any schema change breaks existing databases. The tool will rely on stateless live fetch and push.

## §4 NFRs

| NFR | Verification |
|---|---|
| **Speed** | Execution of `deadliner fetch` (fetching both Moodle and Classroom and rendering output) completes in `< 5s` on a normal university network connection. |
| **Timezone Correctness** | All deadlines must be converted to the local system timezone before classification or sorting. Tested by passing a fixed UTC deadline and fixed timezone to a formatter and asserting on the string output. |
| **Fail Loudly** | If one connector (e.g. Moodle) fails auth, the tool must exit non-zero and print to `stderr`. Verified by running with a revoked token and checking `exit_code != 0`. |

## §5 Anti-patterns I am not repeating
- **Mini #1 (Cashtrack) — Accepting impossible or unvalidated data:** Cashtrack had "best-effort" date parsing that silently accepted impossible dates (like December 32nd). **Our choice:** We strictly enforce standard `datetime` validation and timezone awareness during parsing. Structurally deficient data (e.g. "No due date") is explicitly skipped and logged as a warning, never silently defaulting to the Unix epoch.
- **Mini #2 (Roomwise) — Manager/Helper junk drawer classes:** The Roomwise project suffered from giant `SyncManager` or `DataHelper` classes that violated the Single Responsibility Principle. **Our choice:** We do not use "Manager" or "Helper" suffixes. Our architecture relies on tightly scoped entities like `MoodleFetcher`, `ClassroomFetcher`, and `CalendarGateway`.

## §6 Open questions / risks
**Question escalated from W3 Critic pass:** The Google OAuth 2.0 device flow is supported for CLI tools, but Moodle REST API tokens have no default expiry. Should Deadliner warn the user if the Moodle token hasn't been rotated in more than N days?
**Top Risk:** Rate limiting by Moodle or Google APIs during continuous testing or frequent manual syncs.
**Mitigation:** Provide an explicit caching layer (flat JSON file) for testing purposes, or strictly limit automated test executions to mock APIs.

## §7 Sign-off
- I read this and agree with the scope — ofedkevych, 2026-06-11
- I read this and agree with the scope — surovytsky1vadym-1, 2026-06-11
- I read this and agree with the scope — vkatsel, 2026-06-11
