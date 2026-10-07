# Deadliner Product Backlog & Engineering Roadmap

*Last Updated: 2026-10-08*  
*Current Milestone: Deadliner v2.0*  
*Total Automated Tests: 170 passing*

---

## 🏆 1. Completed in Deadliner 2.0 (Shipped Milestones)

| Feature / Issue | Description | Component | Status |
|---|---|---|---|
| **Native KSE Web Login** | Embedded secure WebView (Edge WebView2 / WebKit) for `schedule.kse.ua` with Google OAuth popup handling and desktop Chrome User-Agent spoofing. Eliminates all DevTools/F12 manual pasting. | `kse_auth.py` | 🟢 Shipped |
| **Safety-Net OAuth Code Exchange** | Automatic listener for GIS `authorization_response` postMessage + direct exchange with `api.kse.today/auth/google`. | `kse_auth.py` | 🟢 Shipped |
| **Token Rotation & 401 Auto-Retry** | Handles KSE `refreshToken` rotation, mixed camelCase/snake_case payloads, and automatic 401 session recovery in `fetch_kse_schedule`. *(From TO_FIX #1)* | `kse_auth.py`, `kse_fetcher.py` | 🟢 Shipped |
| **Event Type Safeguard & Reconciliation** | Tag events with `extendedProperties.private.deadliner_type` (`deadline` vs `schedule`) to ensure class schedule sync never prunes deadline events. *(From TO_FIX #2)* | `calendar_sync.py` | 🟢 Shipped |
| **Moodle Submission Detection** | Detects submitted assignments via Moodle API and highlights them in terminal and calendar metadata. | `moodle_fetcher.py`, `formatter.py` | 🟢 Shipped |
| **Automatic Deadline Rescheduling** | Detects when professors change due dates in Moodle/Classroom and patches existing calendar events while logging `(old_due ➜ new_due)` in `~/.deadliner/sync.log`. | `calendar_sync.py`, `cli.py` | 🟢 Shipped |
| **Windowless Background Auto-Sync** | Daily 24h background sync using Windows Task Scheduler (`pythonw.exe` windowless execution) and native UNIX `crontab`. | `scheduler.py` | 🟢 Shipped |
| **All-in-One CLI Control Center** | Guided interactive CLI menu (`deadliner` / `deadliner menu`, options 1-8) with quick access to all sync operations and credential management. | `cli.py` | 🟢 Shipped |
| **Landing Page Responsive Overhaul** | Mobile drawer navigation, navbar overflow resolution in Ukrainian, language switcher fix (EN/UA bidirectional toggle), and AI-slop cleanup. | `docs/index.html`, `style.css` | 🟢 Shipped |
| **170 Mocked Unit Tests** | Comprehensive test coverage with 0 network dependencies running in under 6 seconds. | `tests/` | 🟢 Shipped |

---

## 🎯 2. Current Sprint (In Progress)

- [x] **Rollback Checkpoint:** Tagged `v2.0-checkpoint-pre-webview` and branch `checkpoint-pre-webview` at commit `5b3e248`.
- [x] **Documentation & Guides Synchronization:** Update `README.md`, `docs/index.html`, and `docs/uk/index.html` to reflect native KSE login and 170 unit tests.
- [x] **Google Verification Appeal Package:** Created `docs/legal/google_oauth_verification_appeal.md` for submission to Google Trust & Safety explaining student pet-project context and `github.io` constraints.
- [ ] **Technical Specification v2 (`docs/specs/v2_spec.md`):** Consolidate PRD and Design Doc into an authoritative, modern specification reflecting all v2.0 capabilities.
- [ ] **Agent & Skills Modular Architecture:** Refactor root `AGENTS.md` into modular agent instructions and skills for pair-programming agents (`.agents/` / `skills/`).

---

## 📋 3. Future Backlog (v2.1+)

### 📦 Distribution & Packaging
- [ ] **PyPI Official Release:** Configure `twine` and GitHub Actions workflow to publish official releases to PyPI (`pip install deadliner`).
- [ ] **Automated Version Update Check:** Lightweight version check (`deadliner update` or startup notification if newer GitHub release is available).

### 🔔 Notifications & Alerts
- [ ] **Native OS Toast Notifications:** Trigger OS-native notifications 2 hours and 30 minutes before critical deadlines (Windows Toast / macOS Notification Center).
- [ ] **Telegram Bot Relay (Optional):** Optional headless Telegram bot integration to forward daily digest or midnight cutoff warnings to a private chat.

### ⚙️ Multi-Profile & Customization
- [ ] **Custom Color Palette Configuration:** Allow students to customize Google Calendar event colors (e.g. Tomato Red, Flamingo, Grape) via config file.
- [ ] **Multi-Program / Multi-Subgroup Support:** Support students pursuing dual degrees or enrolled in multiple academic programs simultaneously.
