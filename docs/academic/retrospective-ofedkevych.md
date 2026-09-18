# Stage 4 Retrospective — Oleksandr Fedkevych (ofedkevych)

## Opening

The thing this term actually taught me is that most production bugs aren't clever.
Nobody in the three minis wrote bad algorithms — they wrote reasonable code in the
wrong scope, or code that swallowed its own errors, or the same function twice with
one character of difference. Every one of those bugs was boring, and every one of
them survived for years because the totals looked fine.
That changed how I write my own code more than any pattern or framework did.
When we built Deadliner, the question I kept asking wasn't "is this elegant" —
it was "if this is wrong, will anyone ever find out?" Cashtrack merged two real
transactions and nobody found out. Shiftlog underpaid an employee and nobody found
out. My bar for P0 became: a failure has to be loud, visible, and tested,
or the feature doesn't ship.

## Anti-pattern 1 — Scope / aggregation bug

**The pattern:** computing a derived value inside the wrong loop scope, so
per-chunk results get summed where the math only works on the merged total.

**Where I saw it:** shiftlog, `src/shiftlog/engine.py:176` — `week_hours = {}`
sits *inside* the per-file loop, and `_fold_into_tally` (`engine.py:283`) then sums
the already-split pay. An employee working one week across two sites gets their
overtime computed per file and then added up. Maria Ivanenko (E001): 34h + 14h =
48h in week 2026-W23, but the report says 48.0 regular / 0.0 OT. She's silently
underpaid 8 hours of the 1.5× premium. The hours column is correct — only the
split underneath is wrong. That's what makes it nasty.

**Where it would have hit us:** the exact same shape exists in Deadliner's
aggregation. We fetch from two sources — `moodle_fetcher` and `classroom_fetcher` —
and US-02 requires one globally sorted list. Sorting each source's list separately
and concatenating would look right on any single-source test and be wrong the first
time a Classroom deadline falls between two Moodle ones. Same bug: per-chunk
operation, merged-total contract.

**How we avoided it:** `sort_assignments` runs once, *after* the merge, in
`src/deadliner/cli.py` (`_collect_assignments` extends one list from both fetchers,
then `_cmd_fetch`/`_cmd_sync` sort the merged result — PR #344 on
`team-typed-aura/stage4`). The tiebreak test
(`tests/test_formatter.py::test_sort_ass3.2 assignments_identical_due_dates_tiebreak_by_course_then_title`)
pins the ordering as a property of the whole list, not of any source.

**Trade-off I evaluated:** sorting inside each fetcher was tempting — it makes each
fetcher's output "nice" on its own. Rejected it precisely because it makes the bug
invisible: every unit test passes and only the merged path is wrong. Fetchers
return unsorted lists; ordering is the aggregator's job, stated once.

## Anti-pattern 2 — Silent failure

**The pattern:** an error path that produces a plausible-looking success value
instead of failing, so wrong data flows downstream with no trace.

**Where I saw it:** shiftlog, `src/shiftlog/parsing.py:262-276` — a timesheet row
with a missing employee id or an unparseable time is just `continue`d. The
docstring says "counted but not raised", but nothing actually counts them. A
malformed row is money that vanishes from payroll silently. Cashtrack (mini 1) was
worse: dedup keyed on date+amount only, so two real same-day transactions got
merged into one — I found that black-box in W1 and it's the same disease.

**Where it would have hit us:** the Moodle API returns HTTP 200 even for an invalid
token, with the error inside the JSON body. The lazy implementation of
`fetch_moodle` returns `[]` on that response — and the CLI happily prints
"No upcoming deadlines." A student with an expired token sees an empty list, trusts
it, and misses a real deadline. That's Deadliner's version of the vanished payroll
row: the worst possible bug for a tool whose whole job is "don't let me miss
things."

**How we avoided it:** `AuthError` in `src/deadliner/models.py`, raised by both
fetchers, with a test that pins the negative space:
`tests/test_moodle_fetcher.py::test_fetch_moodle_invalid_token_does_not_return_empty_list`
(Stage 2/3, PR #312). The CLI prints auth failures to stderr and exits non-zero for
a full failure.

**Trade-off I evaluated:** in Stage 4 we added fault tolerance — one source failing
warns and continues, so a Moodle outage doesn't kill the Classroom fetch. That's
deliberately *not* the same as swallowing: the warning still prints to stderr,
loudly. I considered keeping the hard non-zero exit for any source failure and
rejected it — killing the whole run over one flaky API punishes the user without
informing them any better. Warn-and-continue keeps the signal and the utility.

## Anti-pattern 3 — Duplicated-but-divergent logic

**The pattern:** the same operation implemented twice, drifted one character apart,
with nothing saying whether the divergence is intentional.

**Where I saw it:** roomwise, `src/roomwise/availability.py:67` vs `:79` — two
interval-overlap comparators, `_intervals_overlap_inclusive` and
`_intervals_overlap_strict`, differing by one `<=`. Pricing treats a back-to-back
booking as a conflict; the scheduler doesn't. Shiftlog has the same disease at
scale: three copy-paste parsers (`parsing.py:236-404`) where "if you add a column,
you have to add it in all three" — their own comment admits it.

**Where it would have hit us:** twice, concretely. First: `fetch` and `sync` both
need the fetch-from-both-sources-with-error-handling block — the natural move is
copy-paste, and the moment one copy gets a fix the other doesn't, we're roomwise.
Second: matching calendar events by title in `calendar_sync.py` would have been a
fuzzy second copy of identity logic that drifts from the real one.

**How we avoided it:** extracted `_collect_assignments` in `src/deadliner/cli.py`
so `fetch` and `sync` share the one aggregation path (PR #344), and gave
every synced event a stable `deadliner_id` in its private `extendedProperties`
(`src/deadliner/calendar_sync.py`, `test_sync_patches_existing_event_instead_of_duplicating`)
so identity is defined once, not re-derived by string matching.

**Trade-off I evaluated:** extracting a shared helper for just two call sites is
borderline — the rule-of-three says wait. I did it anyway because the two sites
were about to diverge *in behaviour* (fetch prints, sync pushes) and the shared
part (error tolerance per source) is exactly the part that must never diverge.
Divergence risk, not line count, is what decided it.

## Closing

The decision I'd reverse: shipping the CLI behind `PYTHONPATH=src python -m
deadliner.cli` instead of packaging it properly with a `[project]` table and an
entry point in `pyproject.toml`. It felt like a shortcut that saved an hour in
Stage 3. It then cost us that hour back several times — every README instruction
needs two platform variants, every fresh-clone demo rehearsal has one extra thing
to typo, and the "stranger runs it in 5 minutes" bar got harder instead of easier.
A `pip install -e .` with a real `deadliner` command was maybe twenty lines of
config. The lesson generalizes: developer-experience debt compounds exactly like
code debt, and "we'll package it later" is the same lie as "we'll test it later."

## Ethics framing

Every AI session this term is logged in `ai_usage.txt` with what I kept, what I
rejected, and why — including the sessions where the AI's proposal would have
oversold the product (a README draft claimed Classroom support the CLI didn't
actually have; I rewrote it to state the limitation). That's the AI-usage honesty
topic from W1 in practice, and I think it matters beyond the course: the failure
mode isn't "used AI", it's "presented unverified AI output as checked work." My
rule became that every file:line and every claim the AI drafted gets opened and
confirmed before it ships under my name — the same rule this retrospective was
written under.
