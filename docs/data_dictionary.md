# Data dictionary

Every variable in the analysis data: where it comes from, who is in its universe, what
its codes mean, and where the project uses it.

**Status:** filled in Phase 3, step 5 (2026-09-30).

**Sources for the universe and codes columns.** Value labels come from the DDI codebook
(`data/raw/cps_extract_00001/cps_00001.xml`). The codebook has no `<universe>` element,
so universes come from two places, each marked:
- *DDI:* stated in the variable's description text in the codebook.
- *Data:* which EMPSTAT codes get an NIU code in this extract
  (`python -m src.data.inspect_codes`, section 5; shares only, all months pooled).

"Present" lists the codes that actually occur in extract 1. The DDI labels more codes than
this; for example, the general codes EMPSTAT 20/30 and CLASSWKR 21/24 are never used.
Full code lists for large variables are in the codebook, not here.

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
| Citation | Sarah Flood, Miriam King, Renae Rodgers, Steven Ruggles, J. Robert Warren, Daniel Backman, Etienne Breton, Grace Cooper, Julia A. Rivera Drew, Stephanie Richards, David Van Riper, and Kari C.W. Williams. IPUMS CPS: Version 13.0 [dataset]. Minneapolis, MN: IPUMS, 2025. https://doi.org/10.18128/D030.V13.0 (from the DDI `citReq`; IPUMS also asks that publications be added to http://bibliography.ipums.org/) |

## Requested variables

| Variable | What it is | Preregistration use | Universe | Codes |
|---|---|---|---|---|
| `WTFINL` | Basic monthly person weight | S.6 primary outcome is the sum of this weight | *DDI:* the final weight for basic monthly analyses. *Data:* all 67,917 zero weights are Armed Forces | Continuous, 4 implied decimals (ipumspy applies them) |
| `AGE` | Age at last birthday | S.4 age groups; case selection | Not stated in DDI. *Data:* no NIU; 22-64 by case selection | 00-99 labelled (99 = 99+); present 22-64 |
| `SEX` | Sex | S.14 subgroups | Not stated in DDI. *Data:* no NIU present | 1 Male, 2 Female, 9 NIU; present 1, 2 |
| `EDUC` | Highest year of school or degree completed | S.4, S.14 bachelor's-or-higher | Not stated in DDI. *Data:* no NIU (000/001) or 999 present | 36 labels. Present (16): 002, 010, 020, 030, 040, 050, 060, 071, 073, 081, 091, 092, 111 Bachelor's, 123 Master's, 124 Professional, 125 Doctorate. Which codes count as bachelor's-or-higher is fixed in Phase 5 |
| `EMPSTAT` | Employment status, reference week | S.6 employed, unemployed, not in labor force | Not stated in DDI. *Data:* no NIU (00) present | Present: 01 Armed Forces; 10 At work, 12 Has job, not at work (employed, per DDI text); 21 Unemployed, experienced, 22 Unemployed, new worker; 32 NILF unable to work, 34 NILF other, 36 NILF retired. 00, 20, 30, 31, 33, 35 labelled but absent |
| `LABFORCE` | In the labor force, reference week | S.6 cross-check on the EMPSTAT recode | *DDI:* Armed Forces are NIU. *Data:* NIU = exactly EMPSTAT 01 | 0 NIU, 1 No, 2 Yes |
| `CLASSWKR` | Class of worker, main or most recent job | S.4 wage and salary; S.13 private-sector-only check | *DDI:* current job if employed, else most recent job. *Data:* NIU for all EMPSTAT 22 and 96-99% of NILF; never NIU for employed | Present: 00 NIU; 13, 14 self-employed; 22 private for profit, 23 private nonprofit; 25 federal, 27 state, 28 local government; 26 Armed Forces; 29 unpaid family. S.4 wage and salary = 22, 23, 25, 27, 28 (`design.wage_salary_classwkr`); aggregate codes 20, 21, 24 never used in any year |
| `OCC2010` | Occupation, harmonised to the 2010 Census scheme | S.5 primary occupation code | *DDI (via OCC):* current job if employed, else most recent. *Data:* NIU for Armed Forces, all EMPSTAT 22, 96-99% of NILF, 0.3% of EMPSTAT 21; never NIU for employed | 479 labels (9999 NIU); 475 present, all labelled. Codes collapsed from May 2012 (DDI). List: codebook. Coverage report due Phase 4 |
| `OCC` | Occupation, contemporary codes | S.12 threat 6, the 2020 code change | As OCC2010; 0 = NIU | No labels in DDI. Schemes per DDI: 2011-2019, 2020+. 681 distinct codes; 377 codes shared by 2019 and 2020 |
| `IND1990` | Industry, harmonised to the 1990 Census scheme | S.12 threat 1; S.15 sectors | *DDI (via IND):* current job if employed, else most recent. *Data:* NIU for all EMPSTAT 22 and 96-99% of NILF; Armed Forces all get 952 (Armed Forces, branch not specified) | 246 labels (000 NIU, 998 Unknown); 223 present, all labelled. See `industry_sector_map.csv` |
| `IND` | Industry, contemporary codes | S.15 sector cross-check | As IND1990, except Armed Forces are 0 | No labels in DDI. Schemes per DDI: 2009-2013, 2014-2019, 2020-2024, 2025+ (four inside the window). 325 distinct codes |
| `UHRSWORK1` | Usual hours per week at main job | S.6 hours outcome; S.13 full-time filter | Not stated in DDI. *Data:* 999 for every non-employed record; never 999 for employed | 000 0 hours, 997 Hours vary, 999 NIU/Missing labelled; 1-99 are hours (unlabelled). 997 and 000 occur among the employed; how they enter the hours outcome is fixed in Phase 5 |
| `SCHLCOLL` | School or college attendance, previous week | S.4 student filter | *DDI:* ages 16-24 in basic monthly samples. *Data:* also covers age 25 from 2013 (design notes) | 0 NIU, 1 HS full time, 2 HS part time, 3 college full time, 4 college part time, 5 not attending |

## Variables IPUMS adds automatically

`YEAR`, `SERIAL`, `MONTH`, `HWTFINL` (household weight), `CPSID` (household link),
`ASECFLAG`, `PERNUM`, `CPSIDP` (person link), `CPSIDV` (validated person link).

`CPSIDP` matters later: the CPS follows a household for several months, so the same person
appears repeatedly. Whether this is used for panel checks is `TBD` in Phase 5.

## Exposure file (Eloundou et al.)

Source, hash and download date in `decisions.md`; settings in `config/settings.yaml`
(`design.exposure`). 923 rows, one per O*NET-SOC 2019 code (798 distinct 6-digit SOC).

| Column | What it is | Use |
|---|---|---|
| `O*NET-SOC Code` | O*NET-SOC 2019, 8-digit (e.g. `15-1252.00`) | Merge key; first 7 characters give the 6-digit SOC |
| `Title` | O*NET occupation title | Labels only |
| `dv_rating_beta` | GPT-4 rating, beta = E1 + 0.5*E2 | S.5 primary exposure measure; averaged unweighted within 6-digit SOC |
| `human_rating_beta` | The same beta construct, rated by human annotators | Candidate robustness measure; not used yet |
| `dv_rating_alpha`, `dv_rating_gamma`, `human_rating_alpha`, `human_rating_gamma` | Alpha (E1 only) and gamma (E1 + E2) variants | Not used |

## Occupation crosswalk (Census 2018 code list)

Source, hash and download date in `decisions.md`; settings in `config/settings.yaml`
(`design.occ_crosswalk`). Sheets: `OVERVIEW`, `2018 Census Occ Code List`,
`Summary of 2018 Changes`, `2010 to 2018 Crosswalk ` (trailing space), `Occ Code Changes`.
The project uses `2010 to 2018 Crosswalk `; header on row 4.

| Column | Use |
|---|---|
| `2010 SOC code`, `2010 Census Code`, `2010 Census Title` | Source side; filled only on the first row of a split |
| `2018 SOC Code`, `2018 Census Code`, `2018 Census Title` | Target side; continuation rows of a split have the 2010 side blank. Some SOC codes are Census aggregates (see `design_notes.md`) |

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
- Unemployed people placed by last job (S.6): new entrants (EMPSTAT 22) never have an
  occupation, and 0.3% of experienced unemployed (EMPSTAT 21) have OCC but OCC2010 = 9999.
- IND changes scheme in 2025 as well as 2014 and 2020; IND1990 is harmonised across all three.
