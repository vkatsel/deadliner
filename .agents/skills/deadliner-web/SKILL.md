---
name: deadliner-web
description: >-
  Design guidelines, responsive layouts, bilingual English/Ukrainian workflows, and vector-only asset rules for Deadliner's public landing site and GitHub Pages in docs/.
---

# Deadliner Web & Landing Developer Skill

Use this skill when modifying public-facing web documentation, landing pages (`docs/index.html`, `docs/uk/index.html`), or shared styles (`docs/assets/style.css`).

## Design System Invariants

1. **Vector-Only Branding (No AI Renders):**
   - Strictly vector SVG icons (`docs/assets/logo.svg`).
   - App icon: square 120x120px clean PNG for Google OAuth (`docs/assets/logo.png`).
   - No photorealistic AI renders or fake 3D chrome bubbles.

2. **Pitch-Black & Graphite Palette with Functional Accents:**
   - Backgrounds: `#060609`, `#0D0D12`, `#16161E`.
   - Semantic color accents only:
     - 🔴 **Tomato Red (`#D50000` / `#FF5252`):** Deadlines & urgent cutoffs.
     - 🟢 **Sage Green (`#33B679`):** Theory lectures & verified status.
     - 🔵 **Peacock Blue (`#039BE5`):** Interactive practices & seminars.

3. **Bilingual Synchronization (EN & UA):**
   - Any layout or content update made to `docs/index.html` must be mirrored in `docs/uk/index.html`.
   - Language switchers must maintain bidirectional links:
     - In root pages: `uk/<page>.html`.
     - In `uk/` pages: `../<page>.html`.

4. **Responsive Mobile Navigation:**
   - On screens <= 920px: desktop links collapse into the sleek slide drawer (`#mainNav.open`).
   - The hamburger button (`#navToggle`) and language switch (`.lang-switch`) must remain visible on all screen sizes.
