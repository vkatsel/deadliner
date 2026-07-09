# Stage 4 Retrospective: team-typed-aura
**Author:** surovytsky1vadym

## 1. Opening
If someone told me at the start of the term that I'd be willingly writing unit tests, I would have laughed in their face. Honestly, the biggest lesson I learned wasn't some generic Python syntax—it was how to actually survive working in a shared repo. Learning to define strict boundaries and shared tasks was a trial by fire. Then there's the AI aspect. Prompt engineering isn't just saying "do my homework": it's a relentless cycle of defining constraints, reviewing the output, and realizing the bot just confidently hallucinated an entire complex database architecture into a simple CLI tool. Ultimately, I finally understood the true greatness of Test-Driven Development. Our test suite was the only thing keeping the codebase from being completely infested with my weak 2 AM code or the AI's confident slop. Tests are basically the bouncers of the repo, and I'm honestly glad they were there.

---

## 2. Anti-Pattern: Silent Error Swallowing on Auth Failure
**The Pattern:** Catching an authentication error, deciding it's "too hard" to deal with, and returning an empty list with a `200 OK` so nobody notices the backend is broken.

**Where I saw it in a Mini:** Over in the `cashtrack` mini (`src/api.py:42`), the API literally caught token validation errors and just spat back an empty dataset instead of a `401 Unauthorized`. We actually called this out in our `docs/PRD.md §5` as a mortal sin.

**How it would have manifested in Greenfield:** When I was building `classroom_fetcher.py` (Session 8) and wiring up the Google Auth (Session 11), the easiest, laziest thing to do would be catching a `requests.exceptions.HTTPError` on a 401/403 and returning `[]`. If a student's Google token was revoked, the tool would just print `0 upcoming deadlines found`. The student goes to sleep thinking they're safe, and wakes up with a zero on an assignment.

**How I actually avoided it:** I wrote the US-04 TDD scaffolding (Session 4) explicitly to prevent this. I forced `fetch_classroom` to raise an `AuthError` if the token is garbage (`tests/test_classroom_fetcher.py:15`). Then, in my Stage 4 work, I made sure the CLI catches that and screams at the user to log in again, exiting with a non-zero code.

**The Trade-off:** The user experience gets slightly more annoying because the tool crashes loudly instead of gracefully limping along. But for a deadline tracker, an annoying error message is infinitely better than silently lying to a student about their homework.

---

## 3. Anti-Pattern: The Junk Drawer "Manager" Class (SRP Violation)
**The Pattern:** Creating a massive, god-like "Manager" class that handles network requests, state, formatting, and file I/O all at once because creating separate files felt like too much work.

**Where I saw it in a Mini:** In the `roomwise` mini (`src/sync_manager.py:18`), the legendary `SyncManager` class was a chaotic dumping ground for totally unrelated logic. (Also proudly shamed in our `PRD.md §5`).

**How it would have manifested in Greenfield:** I could have built a massive `GoogleSyncManager` that held the `client_secret.json`, managed the OAuth flow state, fetched the deadlines, formatted them into strings, and pushed them to the calendar all in one massive 500-line class.

**How I actually avoided it:** When I built the Google integration, I kept my components ruthlessly isolated. I wrote `google_auth.py` strictly to handle the OAuth flow and token storage, and `classroom_fetcher.py` to only make HTTP calls and return raw dictionaries. No shared state, no god classes.

**The Trade-off:** It meant I had to pass the token configuration explicitly down the call chain as a dictionary (`{"access_token": token}`) instead of just saving it as `self.token` in a global manager. It adds a bit of parameter passing, but it keeps the codebase sane.

---

## 4. Anti-Pattern: Intertwining Parsing with Business Logic
**The Pattern:** Calculating core business logic inside a file-reading loop or API-fetching loop instead of decoupling it into a separate layer.

**Where I saw it in a Mini:** In the `shiftlog` mini (`src/engine.py:166`), the code calculates overtime *per-file* right inside the parsing loop, mutating local state before folding it into global tallies. This was perfectly called out in PR #3 of the `mini3-shiftlog` repo.

**How it would have manifested in Greenfield:** When I was building `classroom_fetcher.py`, I could have easily done the timezone conversions, sorting, and adding the `(midnight cutoff)` label directly inside the `for course in courses:` loop while fetching from the API.

**How I actually avoided it:** I built `classroom_fetcher.py` to strictly parse the API responses into raw dictionaries and do absolutely zero calculations on the deadlines. The business logic (converting timezones, appending text tags, sorting) happens entirely in `formatter.py` on the complete, pre-grouped data structures (`src/deadliner/formatter.py:22`).

**The Trade-off:** We iterate over the list of assignments twice—once to fetch/parse them from the API, and a second time in the formatter to apply the business rules. It's technically less efficient than doing it all in one loop, but it completely decouples the network layer from the presentation logic.

---

## 5. Closing
If I could reverse one decision in our project, it would probably be the way we handled configuration. We sprinkled environment variables and local `.json` token files all over the place. If I had a time machine, I'd implement a single, unified `Config` class right at the start to validate all credentials upfront. That being said, I actually plan on working on this project further. To be completely honest, we stepped up from P0 to P1 (Google Calendar sync) at the last minute because we looked at the project before presenting, realized a text-only list of deadlines is incredibly boring, and wanted this tool to actually be useful for us in the real world.

## 6. Ethics Framing
This project was a huge wake-up call regarding the professional responsibility and social impact of using AI. It is terrifyingly easy to completely lose track of your own project's architecture because the AI is so eager to write 200 lines of code for you. In our `ai_usage.txt`, we documented how we actively had to fight the AI to stop it from adding unnecessary features and weird databases. If you just blindly accept AI code for an app that tracks university deadlines, and that code silently drops a critical assignment, the student fails their class. The social impact of shipping broken code under your name is real. You can't blame the bot for that; you shipped the code. Moving forward, I plan to use AI much more carefully, treating it as a fast-typing junior dev whose work I am professionally and ethically responsible for reviewing, rather than an all-knowing oracle.
