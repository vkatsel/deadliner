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

### Phase 3: Google Auth Usability & Flexibility (Direct Secrets Paste & Setup Guide) [COMPLETED]
- **Status:** Completed & Tested (commit `0d7a0f6`).
- **Summary:**
  - Added direct interactive pasting of `client_secret.json` content, drag-and-drop file path, and manual Client ID / Secret entry in `_interactive_setup_client_secrets()`.
  - Added sub-option in interactive menu: `deadliner menu` -> `7` (Account & Settings) -> `e` (**Import / Update Google Client Secrets**).
  - Built comprehensive Ukrainian Google Cloud project setup guide in `docs/specs/google_setup_guide.md` and `docs/google_setup_guide.html`.
  - Added fallback embedded configuration support in `google_auth.py`.
  - Covered with 14 unit tests in `tests/test_google_secrets_import.py`.

---

### Phase 4: Comprehensive README & Interactive Menu Documentation [COMPLETED]
- **Status:** Completed (commit `0d7a0f6`).
- **Summary:**
  - Rewrote root `README.md` completely.
  - Documented All-in-One Academic Aggregation, Visual Color Coding (Tomato Red, Sage Green, Peacock Blue), 1-Click KSE Schedule Sync, Cancellation Reconciliation, and 24h Background Auto-Sync.
  - Added complete CLI Reference Table and walkthrough of the interactive terminal menu (`deadliner menu`).
  - Added step-by-step authentication guides and FAQ/troubleshooting for Google 403 / "Unverified app" screen.
  - Fully tested (134 passing unit tests).

---

## Production Readiness Summary

All 4 planned phases are **100% complete**:
- **Phase 1: Moodle Usability** (Defaults, Google SSO tip, normalized URLs)
- **Phase 2: Classroom Config Toggle** (Independent switch via CLI & Menu)
- **Phase 3: Google Auth & Secrets UX** (Direct terminal paste, manual keys, Ukrainian GCP guide)
- **Phase 4: Comprehensive Documentation** (Complete README, web presence, legal docs)
