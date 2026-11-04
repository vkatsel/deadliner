# Stage 4 Retrospective

**Author:** vkatsel

## 1. Opening

Frankly speaking - this term was full of discoveries. From optimizing the work with agentic systems and learning how to use AI effectively, to gaining an understanding of how development process should work in the real world. I went from a full skepticism regarding all those 'useless' PRDs to a bit less skepticism. Joke! In reality I understood that having those documents is an important thing to maintain consistent workflow between the team members and do not forget about what you are building. That's why, those docs must be written carefully and thoroughly.

The second discovery, which is even more important to me - is the importance of testing. I understood that having tests is needed for something and blah-blah, though I missed the whole point. It's a safeguard from your own fingers and neurons of your AI. It helps to not to break your project and be constantly aware that the process is going how it's supposed to go.

Generally, the course was not easy, especially its beginning (as all of your courses tbh), but in the end it turned out to be very insightful and a one, that gives a profound understanding of the process. No pain, no gain!

## 2. Anti-Pattern 1: Silent Failures

- **Where I saw it in a mini:** Mini #1 `cashtrack` - `src/importer.cpp:84`.
- **How it would have manifested in greenfield:** Anywhere, but specifically in `moodle_fetcher.py`. Moodle has a horrible habit to return HTTP 200 OK, even if the token is invalid (returning `{"errorcode": "invalidtoken"}`) or if the server crashes and returns non-JSON page. We could have naively parsed this, which would have resulted in the silent absence of deadlines, and the user would have missed the submission.
- **How I avoided it:** We added an explicit check `if "errorcode" in data:` and `try/except ValueError` around `response.json()`, which throws a controlled `AuthError` or `ConnectionError`. ([commit 5010d6a](https://github.com/CS460-SEP-2026/greenfield/commit/5010d6a))
- **Trade-off / Alternative rejected:** We traded off conciseness of code for reliability by adding extra checks for the sake of robustness.

## 3. Anti-Pattern 2: Tight Coupling

- **Where I saw it in a mini:** Mini #2 `roomwise` - `src/roomwise/facade.py:42`, where facade directly interacted with private fields like `self._scheduler._pricing`
- **How it would have manifested in greenfield:** We could just print text from the inside of fetchers, which would lead to hardcoupling the business logic with CLI interface.
- **How I avoided it:** Fetchers are strictly limited to their own roles. They only return data and use logger for debugging and error messages. All the output formatting and colorization is done in the CLI. ([commit 0cf302f](https://github.com/CS460-SEP-2026/greenfield/commit/0cf302f))
- **Trade-off / Alternative rejected:** It made the code a bit more verbose because we had to pass errors up the chain instead of printing them on the spot, but it allowed us to unit test the fetchers without worrying about capturing stdout.

## 4. Anti-Pattern 3: Logic Duplication

- **Where I saw it in a mini:** Mini #3 `shiftlog` - `src/shiftlog/parsing.py:227`, where three separate parsers were doing almost the same thing but differently.
- **How it would have manifested in greenfield:** As we are working with both Moodle and Google Classroom, we could create different functions for formatting or sorting assignments, doubling the logic.
- **How I avoided it:** We created a single dataclass `Assignment` (`src/deadliner/models.py`). Both fetchers return the same uniform objects, and the CLI works with them through a single function `format_assignment`. ([commit 0cf302f](https://github.com/CS460-SEP-2026/greenfield/commit/0cf302f))
- **Trade-off / Alternative rejected:** We had to spend time to design a common model, which would be a great fit between two platforms, instead of just printing raw responses.

## 5. Closing

One of our decisions was to create a classic CLI with arguments. It is stated in PRD, which we strictly followed. But now, I would merge it all in a single TUI interface with interactive menu, so that our ADHD students don't have to remember the syntax and names of the arguments. That's not really hard to implement and it would be much more user-friendly. However, it is not an initial intent and requires the refactoring of current logic of auth, CLI and interaction with the user. Out of scope - out of mind.

## 6. Ethics Framing

There are two tracks in this one. First - Professional Responsibility and UX. We intentionally paid a lot of attention to error handling and user-friendliness. We added the colourful output, the error messages, help messages and graceful handling of the lost connection. We tried to do our best in the user-flow, following our PRD. There is a lot of room for improvement, though for MVP - that's a decent work. Second vector - is AI usage. The ethical challenge сonsisted of not turning into a blind code-copying machine, but instead using AI as a tool to implement your ideas. I once had an exclusive opportunity to talk with Mykhailo Rohalsky. People asked him a question "What will AI not be able to replace in the next 5 years?". His answer was "The responsibility to make a choice." That's what we had to do.
