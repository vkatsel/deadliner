# Deadliner Documentation Hub

Welcome to the Deadliner documentation repository. This directory serves dual purposes:
1. **GitHub Pages Web Presence:** Static site source for the public landing page and compliance documents deployed at `https://vkatsel.github.io/deadliner/`.
2. **Engineering & Academic Knowledge Base:** System specifications, product backlog, legal compliance artifacts, and academic coursework history.

---

## 📁 Directory Structure

```text
docs/
├── index.html                  # English Landing Page (GitHub Pages root)
├── privacy.html                # English Privacy Policy (Google OAuth verified)
├── terms.html                  # English Terms of Service (Google OAuth verified)
├── google_setup_guide.html     # English Google Cloud OAuth Setup Guide (Web)
├── BACKLOG.md                  # Unified Product Backlog & Release Roadmap
├── README.md                   # This directory index
│
├── uk/                         # 🇺🇦 Ukrainian Bilingual Localization
│   ├── index.html              # Ukrainian Landing Page
│   ├── privacy.html            # Ukrainian Privacy Policy
│   ├── terms.html              # Ukrainian Terms of Service
│   └── google_setup_guide.html # Ukrainian Google Setup Guide
│
├── assets/                     # Visual brand assets & styles
│   ├── logo.svg                # Master vector logo (Clean geometric SVG)
│   ├── logo.png                # 120x120px raster logo for Google OAuth
│   └── style.css               # Shared dark-mode stylesheet & design system
│
├── specs/                      # 📐 Technical Specifications & Architecture
│   ├── README.md               # Specifications Index
│   ├── v2_spec.md              # Deadliner 2.0 Architectural Specification
│   ├── PRD.md                  # Product Requirements Document (v1.0)
│   ├── design_doc.md           # System Architecture & Design Document (v1.0)
│   ├── test_plan.md            # Test Strategy & Traceability Matrix
│   ├── production_readiness_plan.md # Multi-phase production roadmap
│   ├── google_setup_guide.md   # Google Cloud OAuth setup documentation
│   └── devtest_notes.md        # Internal testing notes
│
├── legal/                      # ⚖️ Legal Agreements & Verification
│   ├── README.md               # Legal Documentation Index
│   ├── google_oauth_verification_appeal.md # Google OAuth Appeal Letter
│   ├── privacy.md              # Privacy Policy source (EN)
│   ├── privacy_uk.md           # Privacy Policy source (UA)
│   ├── terms.md                # Terms of Service source (EN)
│   └── terms_uk.md             # Terms of Service source (UA)
│
└── academic/                   # 🎓 Coursework History & Retrospectives
    ├── CONTRIBUTIONS.md        # Individual contribution breakdown
    ├── retrospective-ofedkevych.md
    ├── retrospective-surovytsky1vadym.md
    └── retrospective-vkatsel.md
```

---

## 🌐 Public Web Presence

The documentation site is automatically deployed to GitHub Pages via `.github/workflows/deploy-pages.yml` upon pushes to the main branch:

| Page | English | Ukrainian |
|---|---|---|
| **Landing Page** | [`vkatsel.github.io/deadliner/`](https://vkatsel.github.io/deadliner/) | [`vkatsel.github.io/deadliner/uk/`](https://vkatsel.github.io/deadliner/uk/) |
| **Google Setup Guide** | [`.../google_setup_guide.html`](https://vkatsel.github.io/deadliner/google_setup_guide.html) | [`.../uk/google_setup_guide.html`](https://vkatsel.github.io/deadliner/uk/google_setup_guide.html) |
| **Privacy Policy** | [`.../privacy.html`](https://vkatsel.github.io/deadliner/privacy.html) | [`.../uk/privacy.html`](https://vkatsel.github.io/deadliner/uk/privacy.html) |
| **Terms of Service** | [`.../terms.html`](https://vkatsel.github.io/deadliner/terms.html) | [`.../uk/terms.html`](https://vkatsel.github.io/deadliner/uk/terms.html) |

---

## 📌 Document Management Principles

- **Active Tracking:** All completed features, in-progress items, and future backlogs are maintained centrally in [`BACKLOG.md`](BACKLOG.md).
- **Academic Preservation:** Files located in `academic/` are historical academic records and remain untouched.
- **Strict Compliance:** Any changes to scopes or data flow must be synchronized with files in `legal/` and the public HTML policies.
- **Design System Consistency:** Visual assets must strictly adhere to the vector-only, monochrome + semantic accent rules detailed in [`AGENTS.md`](../AGENTS.md).
