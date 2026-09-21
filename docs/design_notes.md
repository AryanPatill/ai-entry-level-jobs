# Design notes

Facts and decisions that are not changes to the preregistration.
Changes to the preregistration go in docs/deviations.md instead.

## 2026-09-21: recorded before any microdata was downloaded

### October 2025 CPS was never collected
- The U.S. government shutdown (1 Oct - 12 Nov 2025) stopped CPS data collection for
  October 2025. BLS will not collect it retroactively. IPUMS has no October 2025 sample.
- Confirmed from the IPUMS sample catalogue: 187 basic monthly samples, 2011-01 to 2026-08,
  with 2025-10 the only missing month.
- Effect: the event-study bin Sep-Nov 2025 has two months, not three. Preregistration
  Section 9 already says bins use only their available months, so the design is unchanged.
- November 2025 was collected late, with lower response. Flag it in Phase 6 EDA.

### SCHLCOLL may not cover age 25 (student filter, preregistration Section 4)
- IPUMS documentation: in basic monthly samples SCHLCOLL covers ages 16-24
  (16-54 only in the ASEC from 2013).
- Preregistration Section 4 applies the student filter only if the enrollment variable covers
  all ages 22-25. The variable is in the extract so this can be checked on real data.
- Decision deferred to Phase 3 inspection. If age 25 is out of universe, the student-filter
  robustness check is dropped and logged in docs/deviations.md.

### IPUMS sample IDs
- Basic monthly sample IDs use both suffixes: 138 end in "s", 49 in "b". ASEC IDs are
  cpsYYYY_03s. Basic monthly samples are identified by their description
  ("IPUMS-CPS, <Month> <Year>"), never by suffix.