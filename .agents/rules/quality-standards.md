# Deadliner Quality & Engineering Rules

## 1. Architectural Invariants
1. **Local-First & Zero-Knowledge:** Never introduce remote telemetry, analytics, database calls, or proxy servers. All user credentials and tokens stay strictly in `~/.deadliner.json` and `~/.deadliner_google_token.json`.
2. **Fail Loudly:** Never return silent 200 OK or swallow auth failures. Raise `AuthError` or `ConnectionError` with clear troubleshooting hints.
3. **Deterministic Idempotency:** Sync engines must use stable IDs (`extendedProperties.private.deadliner_id`) and isolate event types (`extendedProperties.private.deadliner_type`).

## 2. Code Quality & Testing
1. **Python Standards:** Python 3.10+, strict type annotations (`from __future__ import annotations`, `typing`).
2. **Testing Gate:** Every change must maintain 100% test pass rate (`pytest`). Tests must run with zero external network dependencies using `responses` and `monkeypatch`. Total test suite execution must remain under 6 seconds.

## 3. Git Commit Standard
- **Format:** Conventional Commits: `<type>(<scope>): <message>`.
- **Author:** `vkatsel <vkatsel@kse.org.ua>`.
- **Types:** `feat`, `fix`, `refactor`, `style`, `docs`, `chore`, `ci`, `test`.
