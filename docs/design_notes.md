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

## 2026-09-30: universes and codes for the data dictionary (code coverage only)

Source: the DDI codebook and src/data/inspect_codes.py section 5.

- The DDI codebook has no `<universe>` element. Universes in `data_dictionary.md` come from
  the variable description text or from NIU shares within EMPSTAT codes, and each is marked.
- Section 6 places the unemployed by last occupation. New entrants (EMPSTAT 22) are always
  OCC2010 NIU, so they drop out of occupation cells, which matches the preregistered
  "people with no occupation are excluded". 0.3% of experienced unemployed (EMPSTAT 21) also
  have OCC2010 = 9999 despite a nonzero OCC: a harmonisation gap for the Phase 4 coverage report.
- About 1-3.5% of people not in the labor force carry an occupation and industry (most recent
  job). They are outside the Section 4 sample, which is wage and salary employees.
- IND (raw industry) changes scheme in 2014, 2020 and 2025. The sector map uses IND1990, which
  is harmonised; any IND cross-check (Section 15) must handle all three breaks.
- EDUC, CLASSWKR and UHRSWORK1 each need a code rule in Phase 5 (bachelor's-or-higher codes;
  wage and salary codes; handling of 997 "hours vary" and 000 among the employed). Codes
  present are listed in `data_dictionary.md`. These rules are Aryan's to set.

## 2026-09-30: Census 2010-to-2018 crosswalk structure (codes only, no scores)

- The Census file does contain a 2010 -> 2018 Census occupation conversion, on sheet
  `2010 to 2018 Crosswalk ` (1,068 rows including a legend), with SOC 2010 and SOC 2018 on
  each side. A second file is not needed for 2010 Census -> 2018 Census -> SOC 2018.
- Split codes use blank-continuation rows: the 2010 code sits on the first row and its 2018
  targets on the rows below, with the 2010 columns empty. Parsing must forward-fill the 2010 side.
- 156 of the 568 distinct `2018 SOC Code` values are Census aggregates, not detailed SOC
  codes, so they match nothing in the Eloundou file. Two forms:
  - Numeric codes that are not detailed SOC 2018 occupations (118; mostly broad groups ending
    in 0 such as `11-2030`, plus a few such as `21-1019` and `19-1099`); some list their
    detailed SOC codes inside the title text, for example "Public Relations Managers (11-2032)".
  - Residual codes with X (38, for example `15-124X`, `13-20XX`): "all other in this group
    except codes listed separately".
- 435 distinct detailed SOC codes appear in parentheses inside `2018 Census Title`.
- Military codes (55-xxxx) have no O*NET match; Armed Forces are outside the sample anyway.
- How to expand aggregates to detailed SOC is a design choice and has not been made.