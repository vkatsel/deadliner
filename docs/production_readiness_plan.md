# Production Readiness & UX Improvements Roadmap

## Goal Description
The objective is to make the `deadliner` CLI completely user-friendly, robust, and production-ready for students by eliminating setup friction, providing fine-grained configuration, allowing direct secrets pasting, and delivering comprehensive documentation.

---

## Execution Phases

### Phase 1: Moodle Login Usability [COMPLETED]
- **Status:** Completed & Tested (commit `1ea61cd`).
- **Summary:**
  - Added clean setup header `=== Moodle Login Setup ===`.
  - Added smart default URL `https://teaching.kse.org.ua` with protocol normalization.
  - Descriptive prompts for Username (email/login) and Password (local Moodle password).
  - Helpful troubleshooting tip for users authenticating via Google SSO on the web.
  - Covered with 17 unit tests in `tests/test_auth.py`.

---

### Phase 2: Google Classroom Config Toggle [COMPLETED]
- **Status:** Completed & Tested (commit `1ea61cd`).
- **Summary:**
  - Added `"sync_classroom": bool` support in `~/.deadliner.json` (defaults to `True`).
  - Added CLI commands `deadliner config classroom off`, `on`, and `status`.
  - Integrated toggle into interactive menu (`deadliner menu` -> Option 7).
  - Skipping Google Classroom fetch when disabled, even if Google OAuth token exists.
  - Covered with 11 unit tests in `tests/test_config.py`.

---

### Phase 3: Google Auth Usability & Flexibility (Direct Secrets Paste & Setup Guide)
**Context:** Users currently need to download `client_secret.json` and figure out where to place it on disk. We will eliminate this friction by allowing users to paste secrets directly into the terminal or interactive menu, providing a step-by-step GCP guide, and supporting embedded fallback credentials.

**Detailed Technical Design:**
1. **`docs/google_setup_guide.md` [NEW]**:
   - Foolproof, step-by-step tutorial written in clear Ukrainian.
   - Exact steps with URLs:
     1. Go to Google Cloud Console (`console.cloud.google.com`).
     2. Create a free project (e.g., `deadliner-sync`).
     3. Enable **Google Calendar API** and **Google Classroom API**.
     4. Configure **OAuth Consent Screen** (User type: External, App name: Deadliner, Test users: own email).
     5. Create Credentials: **OAuth client ID** -> Application type **Desktop app**.
     6. Download `client_secret.json` or copy the Client ID & Client Secret.
   - Troubleshooting explanation for the *"Google hasn't verified this app"* screen (Advanced -> Go to Deadliner).
   - Guidance on why Desktop App OAuth is free and secure.

2. **`src/deadliner/google_auth.py`**:
   - Add constants `DEFAULT_CLIENT_ID` and `DEFAULT_CLIENT_SECRET` (fallback if no file/keys provided).
   - Implement `save_client_secrets_json(raw_input_or_dict: str | dict, target_path: Path | None = None) -> Path`:
     - Accepts raw JSON string (e.g., `{"installed": {...}}`), parses and validates required fields (`client_id`, `client_secret`, `auth_uri`, `token_uri`).
     - Accepts dictionary directly.
     - Accepts standalone `client_id` and `client_secret`, constructing a valid Google OAuth installed client config.
     - Saves cleanly formatted JSON to `~/.deadliner/client_secret.json` with parent directory creation and secure permissions.
   - Update `run_oauth_flow()`:
     - Check explicit path -> check `~/.deadliner/client_secret.json` -> check project root -> fall back to in-memory `client_config` dict built from `DEFAULT_CLIENT_ID` / `DEFAULT_CLIENT_SECRET`.

3. **`src/deadliner/cli.py`**:
   - Upgrade `_cmd_login_google(args)`:
     - If no `client_secret.json` is found and no embedded default is configured:
       - Present friendly interactive options:
         1. **Paste JSON content** directly into the terminal (multi-line or single-line).
         2. **Paste path** to downloaded `client_secret.json` (or drag-and-drop file).
         3. **Enter Client ID & Client Secret** manually.
         4. **Open setup guide** in browser (`docs/google_setup_guide.md` or local file).
   - Upgrade `_cmd_menu(args)` (Option 7: Login / Configure Services):
     - Add sub-option to import/update Google Client Secrets without needing to initiate a full login flow.

4. **Testing Plan (`tests/test_google_secrets_import.py`)**:
   - Test saving raw JSON string to `~/.deadliner/client_secret.json`.
   - Test saving Client ID + Secret pair into standard Google JSON format.
   - Test error handling for malformed JSON or missing required fields.
   - Test fallback to embedded credentials when file is absent.
   - Test CLI interactive paste prompt flows.

---

### Phase 4: Comprehensive README & Interactive Menu Documentation
**Context:** The README needs to be rewritten from scratch to showcase the complete feature set of Deadliner, provide visual guides, and document daily workflows for university students.

**Detailed Structure for `README.md`:**
1. **Hero & Badges:**
   - App title, concise elevator pitch, tech stack badges (Python 3.10+, Google APIs, Pytest 100% pass).
2. **Key Features:**
   - 🎯 **All-in-One Academic Aggregation:** Moodle deadlines, Google Classroom tasks, KSE Schedule classes.
   - 🎨 **Visual Color Coding in Google Calendar:**
     - 🔴 **Tomato (Red #11):** Deadlines (ends at cutoff, 15-min warning block).
     - 🟢 **Sage (Green #2):** KSE Lectures & default classes.
     - 🔵 **Peacock (Light Blue #7):** KSE Practices & Seminars.
   - ⚡ **1-Click KSE Schedule Sync:** Clipboard-assisted login bypassing browser CSP restrictions with automatic token refresh.
   - 🧹 **Automatic Cancellation Reconciliation:** Cancelled/shifted KSE classes are automatically deleted from Google Calendar upon sync.
   - ⏰ **24h Background Auto-Sync:** Zero-maintenance automated daily synchronization via native Windows Task Scheduler / Unix crontab, with shortcut logs inspection (`deadliner logs`).
   - ⚙️ **Granular Controls:** Ability to toggle Google Classroom sync (`deadliner config classroom off/on`).
3. **Interactive Menu (`deadliner menu`):**
   - Full walkthrough of the interactive terminal menu (Options 1–8) designed for users who prefer not to memorize CLI arguments.
4. **Complete CLI Reference Table:**
   - `deadliner fetch` & `deadliner sync`
   - `deadliner schedule fetch` & `deadliner schedule sync`
   - `deadliner sync-all`
   - `deadliner config classroom [on|off|status]`
   - `deadliner cron [enable|disable|status|logs]`
   - `deadliner logs`
   - `deadliner login [moodle|google|kse]`
5. **Setup & Authentication Guides:**
   - KSE Schedule (1-click clipboard flow).
   - Moodle (with Google SSO local password tip).
   - Google (link to `docs/google_setup_guide.md`, direct secrets pasting).
6. **Architecture & Development:**
   - Project structure, running tests (`pytest`), design decisions.
7. **Troubleshooting / FAQ:**
   - Google 403 / "Unverified app" screen bypass.
   - Moodle credentials resolution.
   - Background sync troubleshooting on Windows and macOS/Linux.
