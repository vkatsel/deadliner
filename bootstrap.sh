#!/usr/bin/env bash
# bootstrap_greenfield.sh — set up your greenfield namespace + W1 branch + PR.
#
# Run AFTER you've cloned `CS460-SEP-2026/greenfield` and `cd`'d into it.
#
# Usage:
#   ./bootstrap_greenfield.sh <namespace> <my-handle>
#
# Examples:
#   ./bootstrap_greenfield.sh team-banana    bob          # team member
#   ./bootstrap_greenfield.sh alice-skochko  alice-skochko # solo (namespace = handle)
#
# Creates:
#   1. <namespace>/main           (only if it doesn't exist; from origin/main template)
#   2. <namespace>/w1-<my-handle> (your W1 branch)
#   3. A draft PR <namespace>/w1-<my-handle> → <namespace>/main, instructor as reviewer
#
# Prerequisites:
#   - `git` and `gh` installed; `gh auth status` returns OK
#   - You've been added as Write collaborator on the org / team
#   - You're inside a clone of the greenfield monorepo

set -euo pipefail

# ── arg check ─────────────────────────────────────────────────────────────
if [[ $# -ne 2 ]]; then
    echo "usage: $0 <namespace> <my-handle>" >&2
    echo "  namespace = 'team-<slug>' for teams, '<handle>' for solo" >&2
    echo "  my-handle = your GitHub handle" >&2
    exit 2
fi

NS="$1"
HANDLE="$2"

if ! [[ "$NS"     =~ ^([a-z0-9-]{1,30})$ ]]; then
    echo "error: invalid namespace: $NS" >&2; exit 2
fi
if ! [[ "$HANDLE" =~ ^([a-zA-Z0-9-]{1,39})$ ]]; then
    echo "error: invalid handle: $HANDLE" >&2; exit 2
fi

# ── tooling check ─────────────────────────────────────────────────────────
command -v git >/dev/null || { echo "error: git not installed" >&2; exit 1; }
command -v gh  >/dev/null || { echo "error: gh CLI not installed" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "error: gh not authenticated" >&2; exit 1; }

git rev-parse --git-dir >/dev/null 2>&1 || \
    { echo "error: not inside a git repo. cd into your clone of the greenfield monorepo." >&2; exit 1; }

# Sanity-check that we're in the right repo.
ORIGIN=$(git remote get-url origin 2>/dev/null || echo "")
case "$ORIGIN" in
    *CS460-SEP-2026/greenfield*) : ;;
    *) echo "warning: origin = '$ORIGIN' (expected CS460-SEP-2026/greenfield)"; echo "Continuing anyway."; ;;
esac

# ── 1. team trunk branch ──────────────────────────────────────────────────
TRUNK="$NS/main"
W1_BRANCH="$NS/w1-$HANDLE"

git fetch origin --quiet

if git show-ref --verify --quiet "refs/remotes/origin/$TRUNK"; then
    echo "info: $TRUNK already exists. Skipping trunk creation."
    git checkout -B "$TRUNK" "origin/$TRUNK"
else
    echo "info: creating $TRUNK from origin/main template."
    git checkout -B "$TRUNK" origin/main
    git push -u origin "$TRUNK"
fi

# ── 2. W1 branch from team trunk ──────────────────────────────────────────
if git show-ref --verify --quiet "refs/remotes/origin/$W1_BRANCH"; then
    echo "info: $W1_BRANCH already exists. Switching to it."
    git checkout -B "$W1_BRANCH" "origin/$W1_BRANCH"
else
    echo "info: creating $W1_BRANCH from $TRUNK."
    git checkout -B "$W1_BRANCH" "$TRUNK"
    git push -u origin "$W1_BRANCH"
fi

# ── 3. open (or detect existing) draft PR ─────────────────────────────────
EXISTING_PR=$(gh pr list --head "$W1_BRANCH" --base "$TRUNK" --state open \
              --json number --jq '.[0].number' 2>/dev/null || echo "")
if [[ -n "$EXISTING_PR" ]]; then
    echo "info: draft PR #$EXISTING_PR already open."
    gh pr view "$EXISTING_PR" --json url --jq '.url'
else
    gh pr create \
        --draft \
        --base "$TRUNK" \
        --head "$W1_BRANCH" \
        --title "[$NS] W1 @$HANDLE — pitch + green CI" \
        --body "W1 greenfield work for @$HANDLE.

Contents (push commits to this branch by Sun May 17 23:59 EEST):
- motivation.md (per course_pack/templates/motivation.md)
- A minimal project skeleton + one passing test
- A green CI workflow at .github/workflows/ci.yml

Peer review: any classmate (not a teammate) may pick this PR for their W1 peer review, due Mon May 18, 23:59 EEST. Review URLs are submitted via the W1 peer-review activity on Moodle.

Branch must remain mergeable into $TRUNK." \
        --reviewer vskochko
fi

echo ""
echo "✓ bootstrap complete."
echo "  trunk:      $TRUNK"
echo "  W1 branch:  $W1_BRANCH"
echo "  next:       commit your W1 greenfield files here; push; the PR auto-updates."
echo "  remember:   report.md + ai_usage.txt go in your mini-1 fork's W1/ folder, NOT here."
