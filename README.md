# SE460 — Greenfield Monorepo

> **One cohort repo for all greenfield project work.** Every team and every solo student has their own namespace of branches; team trunks are protected; weekly per-member branches are the peer-review surface.

This repo is **not** where legacy work lives. Legacy work (your mini-1, mini-2, mini-3 reading + characterization tests + reports + ai_usage logs) lives in private per-student mini forks. See `course_pack/process/repo_architecture.md`.

---

## Day-0 setup (W1)

```bash
# 1. Clone
git clone https://github.com/CS460-SEP-2026/greenfield.git
cd greenfield

# 2. Run the bootstrap (creates your namespace trunk + W1 branch + draft PR)
./bootstrap.sh <namespace> <my-handle>

# Examples:
#   ./bootstrap.sh team-banana    bob              # team member
#   ./bootstrap.sh alice-skochko  alice-skochko    # solo
```

(`bootstrap.sh` is a copy of `course_pack/tools/bootstrap_greenfield.sh` shipped at this repo's root.)

The bootstrap creates:
1. `<namespace>/main` — your team's (or your) trunk, from the `main` template.
2. `<namespace>/w1-<my-handle>` — your W1 work branch.
3. A draft PR `<namespace>/w1-<my-handle>` → `<namespace>/main` titled `[<namespace>] W1 @<my-handle> — <pitch>`.

---

## Naming conventions — the rules

**Branches:**

```
main                                          # admin-only template
<namespace>/main                              # team or solo trunk (protected)
<namespace>/w<N>-<member>                     # weekly work by a member (solo: omit -<member>)
<namespace>/feature/<short-description>       # ad-hoc feature work
```

`<namespace>` is `team-<slug>` for teams (e.g. `team-banana`) or your `<handle>` for solo.

**PR titles:**

```
[<namespace>] W<N> @<member> — <one-line summary>     # weekly submission
[<namespace>] feat: <short>                            # regular feature work
[<namespace>] stage<N>-v<M>: ready for review          # stage submission marker
```

**Stage tags** (annotated, on `<namespace>/main`):

```
<namespace>/stage1-v1                         # W4 submission
<namespace>/stage1-v2                         # if you used the retry window
<namespace>/stage2-v1                         # W5
<namespace>/stage3-v1                         # W8
<namespace>/stage4-v1                         # W9 frozen-for-defense
```

**Search examples:**

```bash
gh pr list --search "[team-banana]"                  # all of team-banana's work
gh pr list --search "stage1-v1"                      # all Stage 1 submissions
gh pr list --search "W3 @bob"                        # bob's W3 submission
gh pr list --search "W3" --state open --label needs-review
git tag | grep "stage2-v1$"                           # all Stage 2 v1 tags
```

---

## Weekly workflow (team member or solo)

```bash
git checkout <namespace>/main
git pull --rebase
git checkout -b <namespace>/w<N>-<my-handle>

# work in your team / solo subfolder — your team decides the layout
# ...

git add .
git commit -m "W<N>: <one-line>"
git push -u origin <namespace>/w<N>-<my-handle>

# open PR (only first time for the week):
gh pr create --draft \
  --base <namespace>/main \
  --head <namespace>/w<N>-<my-handle> \
  --title "[<namespace>] W<N> @<my-handle> — <short summary>" \
  --reviewer vskochko
```

Every push to your branch auto-updates the PR. The PR is the submission surface.

**Submission deadline: Sunday 23:59 EEST.** Drop `<PR-URL>` in the `#submissions` Slack thread for W`<N>`.

---

## What `main` contains

| File / folder | Purpose |
|---|---|
| `README.md` | this file |
| `bootstrap.sh` | the one-command setup (instructor maintains; copies from `course_pack/tools/`) |
| `.github/workflows/lint.yml` | shared lint on every push (markdown-lint; commit-message format; conflict-marker detection) |
| `.gitignore` | standard ignores |
| `course_pack_pointer.md` | link to the course pack (templates + process docs) |

**Nobody pushes to `main` except the instructor.** Three rulesets enforce:

1. `main`: admin-only updates.
2. `<namespace>/main`: namespace owners + admin; PRs required; no force push; no deletion.
3. `<namespace>/*`: namespace owners + admin push only; no force push; no deletion.

---

## What does NOT live in this repo

| Item | Where it actually lives |
|---|---|
| Weekly `report.md` | Your `mini-N-cashtrack-<handle>` fork at `W<N>/report.md` (private) |
| Weekly `ai_usage.txt` | Same — mini-N fork at `W<N>/ai_usage.txt` (private) |
| Legacy artefacts (black_box.md, competitors.md, characterization tests, reverse_PRD.md) | Mini-N fork at `W<N>/legacy/` (private) |
| Mini-#3 refactor PRs (W6-W7) | Inside each student's `mini-3-*` fork (private; W7 exception opens it briefly) |

The link from this repo TO your private legacy work lives in your mini-N fork's `W<N>/greenfield_link.md` — a one-line file pointing at the PR URL on this monorepo. Your `report.md` (also private) references the PR URL as evidence.

---

## FAQ

**Q: Why can other students see my greenfield work but not my legacy work?**
A: Legacy reading is intimate — your notes, hypotheses, AI prompt logs. Greenfield is collaborative engineering — it's meant to be reviewed by people outside your team. See `repo_architecture.md` §"Why this split".

**Q: Can I push to another team's branch?**
A: No. Branch protection is namespaced. You can `git checkout origin/team-cherry/main` (read), but `git push origin team-cherry/anything` is rejected.

**Q: My W1 branch can't merge into team trunk — there's a conflict.**
A: Fix it. The "mergeable into your team's mainline" requirement is hard: a non-mergeable branch has no PR diff view, so reviewers have nowhere to land line comments. Rebase your branch onto the latest `<namespace>/main` and force-push (force-push is blocked, so this means: open a fresh `<namespace>/wN-<member>-v2` branch and re-open the PR).

**Q: We never actually want to merge `team-X/w<N>-<member>` into our team trunk — the work was exploratory.**
A: Fine. The PR stays open through review, instructor grades on the PR contents, and after grading you can close-without-merge. Grading does NOT depend on the merge happening.

**Q: I'm switching teams between W2 and W4. What happens to my W1 PR?**
A: Up to W4 EOD, dissolutions are allowed (instructor-approved). The instructor moves your W1 PR's branch to the new team namespace, or you close it and re-open under the new namespace. After W4, no team changes — see `team_workflow.md`.
