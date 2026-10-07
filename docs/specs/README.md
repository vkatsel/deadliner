# Technical Specifications & System Architecture

This directory houses the architectural blueprints, technical specifications, and testing matrices for Deadliner.

---

## 📑 Specification Index

| Document | Scope | Description |
|---|---|---|
| [**`v2_spec.md`**](v2_spec.md) | **Deadliner 2.0 (Current)** | Complete technical specification for v2.0: Embedded KSE WebView authentication, Google GIS code exchange listener, refresh token rotation, calendar event type tagging (`deadliner_type`), automatic deadline rescheduling, and windowless background scheduling. |
| [**`PRD.md`**](PRD.md) | **Product Requirements (v1.0)** | Foundational product requirements document defining student user personas, academic portal fragmentation pain points, and core feature definitions. |
| [**`design_doc.md`**](design_doc.md) | **System Architecture (v1.0)** | Architectural blueprint establishing Clean Architecture principles: separation of fetchers, formatters, sync engines, and local credential storage. |
| [**`test_plan.md`**](test_plan.md) | **Test Strategy** | Comprehensive testing strategy and traceability matrix ensuring zero-network fast test execution with mocked responses. |
| [**`production_readiness_plan.md`**](production_readiness_plan.md) | **Release Readiness** | Production verification gates, security checklists, and distribution prerequisites. |
| [**`google_setup_guide.md`**](google_setup_guide.md) | **OAuth Configuration** | Markdown guide detailing Google Cloud Console OAuth 2.0 Client ID setup, consent screen scopes, and credential provisioning. |
| [**`devtest_notes.md`**](devtest_notes.md) | **Development Notes** | Internal developer testing notes, environment considerations, and edge case observations. |

---

## 📐 Invariants & Standards

All modifications to specifications must follow the rules defined in [`.agents/rules/quality-standards.md`](../../.agents/rules/quality-standards.md) and architectural tenets in [`AGENTS.md`](../../AGENTS.md):
- **Local-first privacy:** Zero remote storage, zero telemetry.
- **Fail loudly:** Transparent exceptions for authentication and network errors.
- **Clean architecture:** Single responsibility modules without monolithic manager classes.
