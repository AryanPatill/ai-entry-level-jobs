# Deviations from the preregistration

Every departure from `preregistration.md`, with the date, what changed, and why.
Required by preregistration Section 13 and the project's data and ethics rules.

**Not a deviation:**
- Filling a blank the preregistration told us to fill on a given date (for example the
  data pull month in Section 3). Record it in the preregistration's Section 19 change log.
- Facts learned about the data that the design already accommodates. Those go in
  `design_notes.md`.
- Implementation choices the preregistration did not constrain. Those go in
  `decisions.md`.

**A deviation is:** any change to the sample, outcomes, treatment timing, estimators,
robustness checks, or decision rules, and any preregistered check that turns out to be
impossible to run.

Every entry must also get a row in the preregistration's Section 19 change log.

| Date | Section | What changed | Why | Effect on results |
|---|---|---|---|---|
| 2026-10-17 | 4, 13 | Student filter drops enrolled 22-25-year-olds (SCHLCOLL 1-4), not 22-24, and runs on 2013-01 onward only | Section 4 made the filter conditional on the enrollment variable covering all of 22-25, written when coverage was expected to stop at 24. The data show age 25 is covered from 2013, so the condition holds and the whole treated group is filtered consistently. Decided before any outcome was estimated | Robustness check only; its window starts 2013-01, so it cannot be combined with the 2011-start check |
