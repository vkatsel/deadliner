# Production Readiness & UX Improvements Plan

## Goal Description
The objective is to make the `deadliner` CLI more user-friendly and production-ready by reducing the friction of authentication (Google, Moodle) and providing finer configuration controls (disabling Google Classroom sync). 

## Execution Phases

To ensure changes are trackable and testable, the work is split into three distinct phases.

---

### Phase 1: Moodle Login Usability
**Context:** Students struggle to log into Moodle via the CLI because they don't know what to enter for the `Username` when using Google SSO.
**Proposed Changes:**
- **`src/deadliner/auth.py` (or where Moodle login is handled)**: 
  - Enhance the interactive prompts for `deadliner login moodle`.
  - Add a clear instruction specifying that the `Username` is usually their KSE email address (or the prefix before `@`), and password is their local Moodle password (if set).
**Verification:**
- Run `deadliner login moodle` and verify the prompt is clear and human-readable.

---

### Phase 2: Google Classroom Config Toggle
**Context:** Currently, if a user has authorized Google Calendar, the app unconditionally attempts to fetch assignments from Google Classroom. Users should be able to disable this.
**Proposed Changes:**
- **Config Storage:** Extend the `~/.deadliner.json` schema to support `"sync_classroom": bool` (defaults to `true`).
- **`src/deadliner/cli.py`**:
  - Add subcommands `deadliner config classroom off` and `deadliner config classroom on` to toggle the setting.
  - In the `sync` command logic, check this config value. If `False`, skip the `fetch_classroom` call.
**Verification:**
- **Automated Tests:** Add tests in `tests/test_cli.py` to verify the config toggle updates the JSON file, and that the sync skips Classroom when disabled.
- **Manual Check:** Run `deadliner config classroom off`, then `deadliner sync`, and verify Classroom is skipped in the console output.

---

### Phase 3: Google Auth Embedded Client (Zero-Setup)
**Context:** Users currently need to create their own Google Cloud Project and download `client_secret.json`. This is a huge barrier to entry. We will embed a default "Desktop App" OAuth Client ID directly into the CLI.
**Proposed Changes:**
- **`src/deadliner/google_auth.py`**:
  - Introduce `DEFAULT_CLIENT_ID` and `DEFAULT_CLIENT_SECRET` constants (provided by the project maintainer).
  - Modify `run_oauth_flow` so that if no local `client_secret.json` is found, it automatically falls back to generating a temporary `client_config` dict in-memory using the embedded credentials.
**Verification:**
- **Automated Tests:** Update `tests/test_google_auth.py` to test the fallback logic.
- **Manual Check:** Remove `client_secret.json`, run `deadliner login google`, and ensure the Google Auth browser window opens successfully using the embedded credentials.

---

## Open Questions & Review
- Do we have the default `Client ID` and `Client Secret` ready for Phase 3? If not, Phase 1 and 2 can be executed while the GCP project is being set up by the maintainer.
