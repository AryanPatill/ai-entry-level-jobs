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
  (Update: set by Aryan the same day; see decisions.md and the crosswalk build note below.)

## 2026-09-21: industry sector mapping (preregistration Section 15)

Source: src/crosswalks/industry_sectors.py; full code list in docs/industry_sector_map.csv.

### Rule A: follow NAICS where the 1990 grouping disagrees
- Section 15 names its sectors in NAICS terms, but IND1990 uses the SIC-based 1990 Census
  scheme. Where the two disagree, codes follow NAICS. Chosen by Aryan, 2026-09-21.
- Moved by Rule A: 641 eating and drinking places (retail -> all other, NAICS 722);
  171 newspaper publishing, 800 theaters and motion pictures, 852 libraries, and
  12 veterinary services (all -> sector 1).
- Mixed codes that cannot be split stay in their 1990 group: 172 printing and publishing
  except newspapers stays in manufacturing.
- Code 0 (NIU) gets no sector. Code 952 (Armed Forces, branch not specified; 1,703
  civilians, likely last job military) goes to all other.

### Tech and finance for the threat-1 test (Section 12)
- Section 12 says "drop tech and finance industries" without defining them.
  Interpretation: tech and finance = sectors 1 and 2 from this mapping, so both uses
  share one definition.
- Sector 1 includes some industries that are not "tech" in the everyday sense
  (veterinary services, cinemas, libraries; about 9% of sector 1). Accepted as the cost
  of a consistent, NAICS-based rule.

### 2020 industry code change
- Only 3 IND1990 codes appear before 2020 but not after (600, 782, 801); none appear only
  after. Each stays in the same sector across the break, so sector-level series are not
  affected by the harmonisation.
## 2026-09-30: occupation crosswalk build (codes only; scores never printed)

Source: src/crosswalks/occupation_exposure.py; map in docs/occ_soc_map.csv; coverage in
results/tables/exposure_coverage.md; pinned by tests/test_occupation_exposure.py.

### Split and merge layout
- The main "2010 to 2018 Crosswalk" sheet puts splits source-first (2010 row, then its 2018
  targets) and merges target-first (2018 row, then the 2010 codes it absorbs). Row position
  cannot tell them apart: 0426 sits above its source 0430, and 8990 sits directly under the
  unrelated row for 8900. Forward-filling the 2010 column there left 58 codes with no target and
  attached merge targets to the wrong source.
- "Occ Code Changes" is unambiguous: a blank 2010 code continues a split, a blank 2018 code
  continues a merge. All 28 merge continuations are named in the merge note above them
  (8010, for example, merges into 8025). Every half-filled row of the main sheet appears there.

### Aggregate SOC expansion
- Only 9830 (military) and 9920 (unemployed, never worked) have no SOC code.
- Every residual X group is disjoint across Census codes and fully covered.
- Residuals claim longest-prefix first (an implementation choice; see the 51-9199 disagreement below).

### Title parentheticals vs expansion (test only)
Ruled by Aryan, 2026-09-30: 51-9199 goes to 8990, following the title (explicit override in
`design.occ_crosswalk.soc_overrides`); 53-7065 stays with 9645 as the expansion gives it.
The override changes only the `n_soc_targets` distribution; matched shares are unchanged.

- 137 Census codes name detailed SOC codes in their titles; 134 match the expansion once
  broad codes cited in titles (51-7030) are expanded and a stray space ("(17-3012 )") is allowed.
- Three disagree; none is patched:
  - 51-9199 Production Workers, All Other: the title places it under 8990 Other Production
    Workers (51-91XX); the expansion gives it to 8865 Other Production Equipment Operators
    (51-919X), because the longer residual prefix claims first.
  - 53-7065 Stockers and Order Fillers: named in a title inside the 9570 block (53-70XX), but
    it is 9645's own SOC code, so the exclusion rule keeps it out of 9570. Likely the same
    row-position ambiguity as above.
- 61 of 526 scored 2010 Census codes have some SOC targets without an Eloundou score; their
  score is the mean over scored targets only.

### Unmatched codes
- All unmatched employed OCC2010 codes are "all other" residual occupations whose SOC targets
  (xx-xx99) have no Eloundou score. Every employed OCC2010 code is in the Census 2010 list,
  so the IPUMS May 2012 collapses cause no gaps. Shares are in the coverage report.
