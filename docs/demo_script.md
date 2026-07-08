# Stage 4 Demo Script — team-typed-aura (~6 min, rehearse on a fresh clone)

One shared demo, run once. Driver: pick one person; others narrate their own part.
Everything below is copy-pasteable. Do a full dry run on a FRESH clone the day before.

## Prep (before the session, not part of the 6 min)

- Fresh clone in a scratch dir; dependencies NOT installed (installing is part of the demo).
- One valid Moodle account on teaching.kse.org.ua with ≥2 upcoming deadlines.
- One Google access token (OAuth Playground, scope `calendar.events`) minted <1h before
  the slot, pasted into `~/.deadliner.json` as `google_access_token`.
  (Narrate: "token acquisition is the login google flow — P1, Vadym's part; we mint it
  manually for the demo.")
- Google Calendar open in a browser tab, on the current week.
- Terminal font big enough to read from the back.

## Minute 0–1 — clone and install (proves the README, US-00)

```bash
git clone https://github.com/CS460-SEP-2026/greenfield.git demo && cd demo
git checkout team-typed-aura/main
python -m pip install -r requirements.txt
```

Say: "Four dependencies, one command, README-driven — a stranger can do this in
under five minutes, which was the W8 polish bar."

## Minute 1–2 — the test suite is the safety net (mini lesson #1)

```bash
pytest -q tests/
```

Say: "27 tests, all HTTP mocked, no network. Lesson from the minis: shiftlog had
zero tests and silently underpaid an employee for years — our suite pins exactly
the failure modes the minis shipped: an invalid token must raise, not return an
empty list (test_fetch_moodle_invalid_token_does_not_return_empty_list)."

## Minute 2–3 — interactive login (US-01 auth, P1)

```bash
PYTHONPATH=src python -m deadliner.cli login moodle
```

Type the URL + credentials live. Say: "Token lands in ~/.deadliner.json — no manual
token copying. Auth failure here exits non-zero with a message; silent failure was
the #1 anti-pattern across all three minis."

## Minute 3–4 — fetch: sorted, timezone-correct list (US-01, US-02, US-03)

```bash
PYTHONPATH=src python -m deadliner.cli fetch
```

Point at the output: "Sorted ascending across BOTH sources — sorting happens after
the merge, never per-source; that's the shiftlog per-file aggregation bug avoided.
Times are local, converted BEFORE classification — this deadline at 00:00 carries
the midnight-cutoff label; 23:59 would not."

If a source is down: the warning prints to stderr and the other source still
renders — fault tolerance, show it off rather than apologize.

## Minute 4–5.5 — sync to Google Calendar (P1, the finale)

```bash
PYTHONPATH=src python -m deadliner.cli sync
```

Say: "N created, 0 updated." Switch to the Calendar tab — red 15-minute events,
each ENDING exactly at the deadline, so a midnight cutoff shows as 23:45→00:00
the night before.

Then the money shot — run it again:

```bash
PYTHONPATH=src python -m deadliner.cli sync
```

Say: "0 created, N updated — idempotent. Each event carries a stable deadliner_id
in extendedProperties; we match on identity, never on title. That's the
duplicated-but-divergent lesson from roomwise applied: identity logic exists
once."

## Minute 5.5–6 — close

"P0 shipped and tested in Stage 3; P1 — interactive login, fault tolerance,
calendar sync — landed in Stage 4. Every failure path is loud. Questions."

## Fallback plan (rehearse this too)

- No network / Moodle down: run `pytest -q tests/` + `fetch` with only the Google
  token configured — fault tolerance shows Moodle's warning and Classroom still works.
- Google token expired mid-demo: `sync` prints the auth error to stderr and exits
  non-zero — narrate it as the silent-failure guard working as designed, then re-mint.
- Hard cap discipline: if minute 5 arrives and sync hasn't run, skip the re-run and
  state the idempotency claim verbally with the test name.
