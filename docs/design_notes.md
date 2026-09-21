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

### IPUMS sample IDs
- Basic monthly sample IDs use both suffixes: 138 end in "s", 49 in "b". ASEC IDs are
  cpsYYYY_03s. Basic monthly samples are identified by their description
  ("IPUMS-CPS, <Month> <Year>"), never by suffix.

## 2026-09-21: structural checks on extract 1 (people counts only, no outcomes)

Source: src/data/convert_to_parquet.py and src/data/inspect_codes.py.

### Extract contents
- 12,080,926 person records, 187 months (2011-01 to 2026-08, 2025-10 absent), ages 22-64.
- All 13 requested variables present, plus 9 added automatically by IPUMS.
- Zero nulls in every column. This does NOT mean full coverage: IPUMS codes people
  outside a variable's universe as NIU instead of leaving the cell empty.

### Zero weights are Armed Forces
- 67,917 records have WTFINL = 0 (none negative). All have EMPSTAT = 1 (Armed Forces).
- CPS weights cover the civilian population only.
- Decision for Phase 5: drop EMPSTAT = 1 explicitly. The Section 4 sample (wage and salary
  employees) should exclude them anyway; dropping them explicitly also keeps them out of
  unweighted cell counts and the unweighted-counts robustness check (Section 13).

### SCHLCOLL covers ages 22-25 from 2013 (student filter, preregistration Section 4)
- Correction: the pre-download note expected SCHLCOLL to stop at age 24 in basic monthly
  samples, based on IPUMS documentation. The data shows otherwise.
- Civilian NIU share: ages 22-24 are 0% NIU in every year 2011-2026. Age 25 is 100% NIU in
  2011 and 2012, and 0% NIU from 2013 onward.
- The small NIU counts at ages 22-24 (about 2,500-3,000 each, pooled) are Armed Forces.
- Section 4's condition (enrollment variable covers all ages 22-25) is met for 2013 onward,
  which contains the whole main window (2015+). The student-filter robustness check runs
  as preregistered. No deviation.
- Limit: the student filter cannot be combined with the 2011-start robustness check,
  because 2011-2012 lack age-25 coverage. Section 13 lists them as separate checks.

### Monthly sample size fell over the window
- Average records per month (ages 22-64): 76,221 (2011), 73,322 (2015), 65,311 (2019),
  57,742 (2020), 54,891 (2022), 52,940 (2024), 48,176 (2026, 8 months).
- Pattern: steady decline 2011-2019, a step down in 2020, continued decline after.
- Effect: post-treatment months have roughly 25-35% fewer records than the 2015 baseline,
  so precision is lowest where the effect would appear. Feeds the minimum detectable
  effect check at the end of Phase 5 (preregistration Section 16).