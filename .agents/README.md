# Deadliner Agent & Customization Architecture

This directory contains modular agent rules, skills, and runbooks adhering to the **Antigravity Customization System** standards.

## Directory Structure

```text
.agents/
├── README.md                          # This directory documentation
├── rules/
│   └── quality-standards.md           # Invariant architectural and engineering rules
└── skills/
    ├── deadliner-cli/
    │   └── SKILL.md                   # Core CLI Developer (Python, TDD, APIs, pywebview)
    ├── deadliner-web/
    │   └── SKILL.md                   # Web & Landing Developer (HTML5/CSS3, responsive, vector-only)
    └── deadliner-legal/
        └── SKILL.md                   # Legal & Compliance Specialist (Google verification, privacy)
```

## How It Works

- **Hierarchical Rules:** `.agents/rules/` contains rules that apply across the entire codebase alongside the root `AGENTS.md`.
- **Progressive Disclosure Skills:** `.agents/skills/<name>/SKILL.md` are loaded on demand by pair-programming agents based on task context.
- **Role Alignment:**
  - `deadliner-cli`: Python core CLI, APIs, testing, synchronization logic.
  - `deadliner-web`: Responsive landing page, GitHub Pages, design system compliance.
  - `deadliner-legal`: Privacy policies, terms of service, Google OAuth verification appeals.
