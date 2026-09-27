# Deadliner Documentation Hub

Welcome to the Deadliner documentation directory. This directory serves both as the source for the public GitHub Pages landing website and as the structured repository for architectural specifications, legal compliance, and academic records.

---

## 📁 Directory Structure

```text
docs/
├── index.html                  # Public Landing Page (GitHub Pages root)
├── privacy.html                # Public Privacy Policy (Google OAuth compliant)
├── terms.html                  # Public Terms of Service (Google OAuth compliant)
├── README.md                   # This directory index
│
├── assets/                     # Visual brand assets and stylesheets
│   ├── logo.png                # Official 120x120px square app logo
│   └── style.css               # Shared responsive dark theme stylesheet
│
├── specs/                      # Technical specifications & architecture
│   ├── PRD.md                  # Product Requirements Document
│   ├── design_doc.md           # Architecture & Design Document
│   ├── test_plan.md            # Comprehensive Test Strategy & Traceability Matrix
│   ├── devtest_notes.md        # Developer testing and implementation logs
│   └── production_readiness_plan.md # Multi-phase production roadmap
│
├── legal/                      # Markdown source of legal documentation
│   ├── privacy.md              # Privacy Policy source
│   └── terms.md                # Terms of Service source
│
└── academic/                   # University coursework & team retrospectives
    ├── CONTRIBUTIONS.md        # Individual contribution breakdown
    ├── retrospective-ofedkevych.md
    ├── retrospective-surovytsky1vadym.md
    └── retrospective-vkatsel.md
```

---

## 🌐 Public Web Presence (GitHub Pages)

The public site is deployed automatically via `.github/workflows/deploy-pages.yml` upon pushes to `main` and `deadliner-2.0`:
- **Home:** `https://vkatsel.github.io/deadliner/`
- **Privacy Policy:** `https://vkatsel.github.io/deadliner/privacy.html`
- **Terms of Service:** `https://vkatsel.github.io/deadliner/terms.html`
