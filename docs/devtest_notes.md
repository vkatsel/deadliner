# Stage 3: DevTest Notes

## Component 1: Moodle Fetcher & Domain (vkatsel)
- **Implementation Strategy:** Integrated the Moodle REST API `core_calendar_get_action_events_by_timesort` endpoint using the `requests` library. Implemented custom error handling to parse `errorcode` from the JSON body, as Moodle returns HTTP 200 even for invalid tokens.
- **Testing Strategy:** Used the `responses` library to mock HTTP calls in `test_moodle_fetcher.py`. This allowed verifying the happy path and edge cases (like `invalidtoken` raising `AuthError`) without touching the real Moodle server.
- **Design Divergences:** Added the `AuthError` exception explicitly into `models.py` (which wasn't deeply specified in Stage 1 but is strictly required for the fetcher contracts to communicate auth failures).

## Component 2: Classroom Fetcher & Git Hooks (surovytsky1vadym-1)
- **Implementation Strategy:** The `pre-push` hook and `make ci` pipeline were already in place from Component 1's repo setup, so this component's remaining scope was `fetch_classroom`. Implemented it by calling the real Google Classroom REST API (`GET /courses`, then `GET /courses/{id}/courseWork`) directly with `requests`, mirroring `moodle_fetcher.py`'s style (module logger, plain `requests` calls, shared `AuthError`/`ConnectionError`) instead of pulling in the `googleapiclient`/`google-auth` SDKs, since the design doc only requires an OAuth credentials dict as input.
- **Testing Strategy:** Rewrote `test_classroom_fetcher.py` to import `fetch_classroom` and `AuthError` from `src` and mock both Classroom REST endpoints with the `responses` library (the same approach as `test_moodle_fetcher.py`), instead of the original stub's magic-string-token branching, which had no way to actually exercise the API-parsing code path.
- **Design Divergences:** Unlike Moodle (which returns HTTP 200 with an `errorcode` field for a bad token), Google Classroom returns HTTP 401 for a revoked/expired token, so `AuthError` is raised on a 401 response rather than by inspecting the JSON body. A missing `access_token` in the credentials dict is treated as an auth failure before any HTTP call is made. `courseWork` items without a `dueDate` are skipped (logged as a warning), and a missing `dueTime` defaults to 23:59 UTC. Also fixed two cross-cutting gaps blocking CI for everyone: added `requirements.txt` (`pytest`, `requests`, `responses`, `ruff` — previously undeclared anywhere) and updated `.github/workflows/test.yml` to trigger on `team-typed-aura/stage3` and run `make ci` instead of a bare `pytest` subset.

## Component 3: CLI, Formatter & Tooling Config (TBD)
- **Implementation Strategy:** [TODO: Describe CLI and formatting logic]
- **Testing Strategy:** [TODO: Describe testing strategy for CLI]
- **Design Divergences:** [TODO: Did anything change from `design_doc.md`?]
