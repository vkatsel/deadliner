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

### Phase 3: Google Auth Usability & Flexibility (Direct Secrets Paste & Setup Guide)
**Context:** Users currently need to download `client_secret.json` and figure out where to place it. We will make Google authentication frictionless by allowing direct paste of secrets, providing a step-by-step GCP guide, and supporting embedded fallback credentials.
**Proposed Changes:**
- **`docs/google_setup_guide.md` [NEW]**: Detailed, step-by-step guide in Ukrainian for creating a GCP project, enabling Calendar & Classroom APIs, setting up Desktop App OAuth, and downloading credentials.
- **`src/deadliner/google_auth.py`**:
  - Add `DEFAULT_CLIENT_ID` / `DEFAULT_CLIENT_SECRET` fallback support.
  - Implement `save_client_secrets_json()` to validate and save pasted JSON or credentials directly to `~/.deadliner/client_secret.json`.
- **`src/deadliner/cli.py`**:
  - Upgrade `_cmd_login_google`: allow pasting raw JSON directly into the terminal, entering a file path, or entering Client ID & Secret manually.
  - Add Google Secrets management option under Option 7 in `deadliner menu`.
**Verification:**
- **Automated Tests:** Add `tests/test_google_secrets_import.py` and update `tests/test_google_auth.py` to test raw JSON parsing, manual credentials entry, and fallback logic.
- **Manual Check:** Run `deadliner login google`, paste a client secrets JSON string, and verify it correctly creates `~/.deadliner/client_secret.json` and initiates OAuth.

---

### Phase 4: Comprehensive README & Interactive Menu Documentation
**Context:** The README needs to be rewritten to reflect the complete set of features (Moodle, KSE Schedule with Sage/Peacock coloring, cancellation reconciliation, 24h cron auto-sync, Classroom toggle, interactive menu, and authentication guides).
**Proposed Changes:**
- **`README.md`**:
  - Product overview & visual indicators.
  - Interactive menu guide (`deadliner menu`).
  - Full CLI command reference.
  - Setup guides for Moodle, Google, and KSE Schedule.
  - Troubleshooting & FAQ.
**Verification:**
- Markdown linting and link verification.

---

## Open Questions & Review
- All phases are fully defined and ready for execution.
