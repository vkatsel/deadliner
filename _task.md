## **Stage 3 — Implementation (15 pts)**

**Due:** Sunday July 5, 2026, 23:59 EEST (this activity is authoritative). **Submit:** the URL of your **open** pull request `<namespace>/stage3 → <namespace>/main` into this activity. **Worked examples:** `cashtrack` , `roomwise` , and your refactored `shiftlog` mini. **Full brief + rubric + checklist:** `project/Stage3_brief.md` in the course-pack repo.

Stage 3 is where the thread pays off. In **Stage 1** you wrote the contract ( `PRD.md §3.1` Given/When/Then + `design_doc.md §3` API). In **Stage 2** you turned every P0 story into tests that were **red on purpose** . This stage you write the production code that makes those **red tests go green** — shipped with the **tooling you stood up in the W7 practice** ( `make ci` + the pre-push hook) now enforcing green on `main` .

This is the one stage with **real working software** at the end: a classmate clones your repo, runs one command, and your P0 stories _work_ . Nothing new is invented — Stage 3 is the **execution** of the design you defended and the test plan you wrote.

## **The load-bearing idea: green for the right reason, faithful to the design**

Stage 2’s thesis was _red on purpose_ . Stage 3’s is its mirror — **green on purpose.**

- ✅ `test_reporter_by_category_sums_each_group` passes because `Reporter.by_category` now **does the thing** , built on the entity from your design doc.

- ❌ The same test passes because the method **returns the literal the assertion wants** , or because you **edited the test down** to match broken code. That is green for the wrong reason — it proves nothing.

A P0 story is **done** when its tests pass _and_ the code that passes them is the entity model and API you committed to in Stage 1. If implementation forced a design change — normal — **say so in** **`docs/devtest_notes.md`** . An undocumented divergence reads as “the design was theatre.”

## **What you ship**

All in your greenfield monorepo, on branch `<namespace>/stage3` , as **one open PR →** **`<namespace>/main`** :

- **Part A — the P0 implementation** ( `src/` ) — every P0 story from `PRD.md §3.1` working, on the `design_doc.md §2–3` entities and API. P0 first, and **P0 only is required** — P1/P2 are bonus, not the bar.

- **Part B — the test suite goes green** ( `tests/` ) — the Stage-2 tests now **pass** (happy-path **and** edge cases). Any P0 you legitimately cut → downgrade it in the PRD and say so; never drop a P0 silently.

- **Part C — tooling on** **`main`** — a one-command pipeline ( `make ci` / `run_ci.sh` from W7) running **lint + formatter/static-analysis + the test suite** , green; the versioned **`.githooks/pre-push`** hook installed via `git config core.hooksPath .githooks` .

- **Part D —** **`docs/devtest_notes.md`** (~1 page) — how you developed and verified P0, what `make ci` enforces, and **what moved from the Stage-1 design and why** (an honest design-vs-implementation note).

- **Gate —** **`docs/CONTRIBUTIONS.md`** — the Stage-3 contribution block (C.1), refreshed.

- **Gate —** **`ai_usage.txt`** — AI as implementer / pair-programmer, including **≥1 AI proposal you rejected** (an over-built abstraction, a wrong-shortcut “fix” that passes the test but breaks the contract, a needless dependency) and **why** .

**No tag** — the branch name `<namespace>/stage3` is the indicator (same as Stage 1/2). **Do not merge the PR yourself** ; the instructor reviews it open and merges into `<namespace>/main` after grading.

## **What the rubric rewards most**

- **Tests cover the target, including invalid-input & empty-argument edge cases (4 pts)** — green, and the traceability matrix still maps every P0 to ≥1 passing test.

- **Implementation correctness (3 pts)** — P0 actually works; the tests pass for the **right reason** .

- **Implementation matches the design (3 pts)** — entities/API as in `design_doc.md §2–3` ; divergences documented, not silent.

- **Code style & submission format (3 pts)** — clean code (PRD §5 anti-patterns genuinely avoided), templates/layout honoured, branch + open-PR convention.

## **How to submit**

Paste the **open PR URL** ( `<namespace>/stage3 → <namespace>/main` ) into this activity by the deadline.

## **Early submission policy**

Early submission policy is applied if you sent 3days or more before the deadline you may address the comments

## **Teams**

One **team grade** per stage. You personally receive it only if (a) the contribution block is concrete, evidence-backed, with distinct ownership, **and** (b) your own contribution spans the project (code _and_ tests _and_ tooling). A member confined to a single slice receives **less than** the team grade; a vague or unverifiable block means credit is read conservatively from git history.

## **Grading (15 pts)**

|     | **Criterion**                                                                                            | **Pts** |
| --- | -------------------------------------------------------------------------------------------------------- | ------- |
|     | Implementation correctness — P0 works<br>(Stage-2 tests pass for the right reason)                       | 3       |
|     | Implementation matches the design —<br>entities/API as in`design_doc.md §2–3`;<br>divergences documented | 3       |
|     | Code style & submission format — clean<br>code, templates/layout, branch + open-PR<br>convention         | 3       |
|     | Tests cover the target functionality,<br>including invalid-input and<br>empty-argument edge cases        | 4       |
|     | Devtest strategy described<br>(`docs/devtest_notes.md`)                                                  | 2       |

**Critical:** a test that passes because it was **edited to match broken code** (or asserts a hard-coded literal) is green for the wrong reason — no correctness credit for that story. An implementation that **silently abandons the Stage-1 design** loses the design-fidelity line. A CI pipeline that is **red** , or that **passes even when tests fail** ( `|| true` , swallowed exit code, no `set -e` ), is not green tooling; a hook not wired via `core.hooksPath` does not count. A P0 **neither implemented nor downgraded** loses traceability. `ai_usage.txt` → missing **0 on Stage 3** (the instructor resolves filename quirks first).
