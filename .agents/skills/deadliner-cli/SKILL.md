---
name: deadliner-cli
description: >-
  Workflows, conventions, and test-driven procedures for modifying Deadliner's core Python CLI, API integrations (Moodle, Google Classroom, KSE Schedule), synchronization logic, and test suite.
---

# Deadliner Core CLI Developer Skill

Use this skill when developing or debugging core Python modules in `src/deadliner/` and tests in `tests/`.

## Architecture Map

```text
src/deadliner/
├── auth.py              # Moodle web service auth & token validation
├── calendar_sync.py     # Google Calendar event creation, patching, & reconciliation
├── classroom_fetcher.py # Google Classroom coursework & courses fetcher
├── cli.py               # CLI entrypoint, argument parsing, & interactive menu
├── formatter.py         # Terminal output formatting & deadline urgency tagging
├── google_auth.py       # Google OAuth2 InstalledAppFlow & secrets import
├── kse_auth.py          # KSE Schedule pywebview login, popup handling, & token rotation
├── kse_fetcher.py       # KSE Schedule REST API client (schedule.kse.ua / api.kse.today)
├── models.py            # Dataclasses (Assignment, ScheduleClass, AuthError, etc.)
├── moodle_fetcher.py    # Moodle core_calendar API client & submission detection
├── path_util.py         # OS-native PATH configuration & executable detection
└── scheduler.py         # OS task scheduler (Windows schtasks with pythonw, UNIX cron)
```

## Core Procedures

### 1. Code -> Refactor -> Test Cycle
Always write unit tests in `tests/` alongside code modifications:
```powershell
pytest
```
Ensure all 170+ tests pass with zero network calls (use `responses` and `monkeypatch`).

### 2. KSE Schedule OAuth & PyWebView
- On Windows, Edge WebView2 is used with monkeypatched `NewWindowRequested` (`args.set_Handled(False)`).
- Always ensure standard Desktop Chrome User-Agent is passed to `AdditionalBrowserArguments` and `webview.start(..., user_agent=...)`.
- Always provide `--clipboard` and `--manual` CLI fallbacks.

### 3. Google Calendar Synchronization Invariants
- `extendedProperties.private.deadliner_id`: SHA-256 hash or deterministic UUID.
- `extendedProperties.private.deadliner_type`: `"deadline"` or `"schedule"`.
- When rescheduling: update existing event start/end times in place; never delete and recreate.
