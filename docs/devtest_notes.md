# Stage 3: DevTest Notes

## Component 1: Moodle Fetcher & Domain (vkatsel)
- **Implementation Strategy:** Integrated the Moodle REST API `core_calendar_get_action_events_by_timesort` endpoint using the `requests` library. Implemented custom error handling to parse `errorcode` from the JSON body, as Moodle returns HTTP 200 even for invalid tokens.
- **Testing Strategy:** Used the `responses` library to mock HTTP calls in `test_moodle_fetcher.py`. This allowed verifying the happy path and edge cases (like `invalidtoken` raising `AuthError`) without touching the real Moodle server.
- **Design Divergences:** Added the `AuthError` exception explicitly into `models.py` (which wasn't deeply specified in Stage 1 but is strictly required for the fetcher contracts to communicate auth failures).

## Component 2: Classroom Fetcher & Git Hooks (TBD)
- **Implementation Strategy:** [TODO: Describe implementation]
- **Testing Strategy:** [TODO: Describe testing]
- **Design Divergences:** [TODO: Did anything change from `design_doc.md`?]

## Component 3: CLI, Formatter & Tooling Config (TBD)
- **Implementation Strategy:** [TODO: Describe CLI and formatting logic]
- **Testing Strategy:** [TODO: Describe testing strategy for CLI]
- **Design Divergences:** [TODO: Did anything change from `design_doc.md`?]
