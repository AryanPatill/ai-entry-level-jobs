# Data dictionary

Every variable in the analysis data: where it comes from, who is in its universe, what
its codes mean, and where the project uses it.

**Status:** skeleton. The columns and sources below are confirmed from IPUMS CPS extract 1.
The universe and code sections marked `TBD` are filled in Phase 3, step 5, from the DDI
codebook (`data/raw/cps_extract_00001/cps_00001.xml`), not from memory.

## Source

| | |
|---|---|
| Collection | IPUMS CPS, basic monthly samples |
| Extract | 1, submitted and downloaded 2026-09-21 |
| Definition | `docs/extract_definition.json` (committed) |
| Coverage | 187 monthly samples, 2011-01 to 2026-08; 2025-10 was never collected |
| Case selection | AGE 22-64 |
| Structure | Rectangular on person, fixed width |
| Records | 12,080,926 |
| Citation | `[verify]` IPUMS CPS citation text required by their terms; add before Phase 13 |

## Requested variables

| Variable | What it is | Preregistration use | Universe | Codes |
|---|---|---|---|---|
| `WTFINL` | Basic monthly person weight | S.6 primary outcome is the sum of this weight | Civilians; Armed Forces have weight 0 | Continuous |
| `AGE` | Age in years | S.4 age groups; case selection | All | 22-64 in this extract |
| `SEX` | Sex | S.14 subgroups | All | TBD |
| `EDUC` | Educational attainment | S.4, S.14 bachelor's-or-higher | All | TBD |
| `EMPSTAT` | Employment status | S.6 employed, unemployed, not in labor force | All | 1 = Armed Forces; rest TBD |
| `LABFORCE` | Labor force status | S.6 cross-check on the EMPSTAT recode | All | TBD |
| `CLASSWKR` | Class of worker | S.4 wage and salary; S.13 private-sector-only check | Employed and last job | TBD |
| `OCC2010` | Occupation, harmonised to the 2010 scheme | S.5 primary occupation code | Employed; unemployed by last job | TBD; coverage report due Phase 4 |
| `OCC` | Occupation, contemporary codes | S.12 threat 6, the 2020 code change | Same as OCC2010 | 2011-2019 use the 2010 scheme; 2020+ use the 2017 scheme |
| `IND1990` | Industry, harmonised to the 1990 scheme | S.12 threat 1; S.15 sectors | Employed; unemployed by last job | 223 codes in this extract; see `industry_sector_map.csv` |
| `IND` | Industry, contemporary codes | S.15 sector cross-check | Same as IND1990 | TBD |
| `UHRSWORK1` | Usual hours per week at main job | S.6 hours outcome; S.13 full-time filter | Employed | TBD, includes an NIU code |
| `SCHLCOLL` | School or college attendance | S.4 student filter | Ages 16-24 through 2012; includes 25 from 2013 | 0 NIU, 1-2 high school, 3-4 college, 5 not attending |

## Variables IPUMS adds automatically

`YEAR`, `SERIAL`, `MONTH`, `HWTFINL` (household weight), `CPSID` (household link),
`ASECFLAG`, `PERNUM`, `CPSIDP` (person link), `CPSIDV` (validated person link).

`CPSIDP` matters later: the CPS follows a household for several months, so the same person
appears repeatedly. Whether this is used for panel checks is `TBD` in Phase 5.

## Derived variables

Added as the analysis is built. Each entry names the module that creates it.

| Variable | Created by | Definition |
|---|---|---|
| `sector` | `src/crosswalks/industry_sectors.py` | IND1990 mapped to the six Section 15 sectors, Rule A |
| | | further entries added in Phases 4 and 5 |

## Known coverage facts

Full detail in `design_notes.md`.

- IPUMS codes people outside a variable's universe as NIU rather than leaving a cell empty,
  so a zero null count never means full coverage.
- 67,917 records have `WTFINL` = 0; all are Armed Forces (`EMPSTAT` = 1). Dropped in Phase 5.
- Records per month fall from about 76,000 (2011) to about 48,000 (2026).
