# Plan

Phase status and current position. Updated at the end of every step, before the commit.
Phase detail lives in `preregistration.md` (design) and `architecture.md` (mechanics).

## Where the project stands

- **Current phase:** 5, cleaning and sample construction
- **Last completed step:** Phase 5 steps 4-5, outcome sums and subgroup columns in the panel
- **Next step:** Aryan confirms the unemployment and full-time interpretations (decisions.md,
  2026-10-04) and whether to add the student-filter column; then Phase 6

## Phases

| Phase | Name | Main output | Status |
|---|---|---|---|
| 0 | Setup questions | Environment recorded | Done |
| 1 | Research design | `preregistration.md` v1.0 | Done |
| 2 | Environment | Repo, venv, git, config | Done |
| 3 | Data acquisition | Raw Parquet, sector map, data dictionary | Done |
| 4 | Crosswalks and exposure mapping | Exposure-mapped occupations, coverage report | Done |
| 5 | Cleaning and sample construction | Analysis panel | In progress |
| 6 | EDA and descriptive replication | Trend figures, descriptive comparison | Not started |
| 7 | Identification strategy | Causal diagram, assumptions, threats-to-tests table | Not started |
| 8 | Estimation | DiD, triple-difference, event-study tables | Not started |
| 9 | Robustness and falsification | Placebo, sensitivity, inference tables | Not started |
| 10 | Heterogeneity | Subgroup results | Not started |
| 11 | Agent layer | LangGraph pipeline with typed handoffs | Not started |
| 12 | Agent evaluation | Mapper accuracy, Skeptic catch rate | Not started |
| 13 | Delivery | Tests, one-command pipeline, dashboard, README, write-up | Not started |
| 14 | Ongoing extensions | Monthly refresh, postings data, new measures | Not started |

## Phase 3 steps

| Step | What | Status |
|---|---|---|
| 1 | Extract definition built from the preregistered design | Done |
| 2 | Extract submitted and downloaded (IPUMS CPS extract 1) | Done |
| 3 | Fixed-width converted to Parquet; structural checks | Done |
| 4a | IND1990 codes listed with codebook labels | Done |
| 4b | Codes mapped to the six sectors (Rule A) | Done |
| 5 | Data dictionary | Done |

## Phase 4 steps

| Step | What | Status |
|---|---|---|
| 1 | Exposure file downloaded, SHA-256 verified; column and code system set | Done |
| 2a | Census crosswalk file chosen, downloaded, hash-verified; sheets inspected | Done |
| 2b | OCC2010 -> SOC 2018 map (Occ Code Changes for changed codes; BLS expansion) | Done |
| 3 | Exposure merged to OCC2010; coverage report (`results/tables/exposure_coverage.md`) | Done |
| 4 | Exposure quintiles (`results/tables/exposure_quintiles.md`) | Done |

## Phase 5 steps

| Step | What | Status |
|---|---|---|
| 1 | Quintile cutoffs frozen; Q1/Q5 face-validity lists | Done |
| 2 | Main panel (employed wage and salary, occ x age group x month) and cell-size report | Done |
| 3 | Minimum detectable effect, pre-period only (`results/tables/mde.md`) | Done |
| 4 | Secondary outcomes in the panel: unemployment and hours sums | Done |
| 5 | Subgroup and robustness columns: bachelor's or higher, sex, private only, full time | Done |
| 6 | Student-filter column (Section 13; supported for 2013+, design_notes.md 2026-09-21) | Not started; not in Aryan's step-5 list |

## Commitments carried into later phases

- Phase 6: "hours vary" (UHRSWORK1 997) share by quintile x period, before the hours outcome
  is interpreted (design_notes.md, 2026-10-04).
- Phase 8: the equivalence test (TOST against ±5%, alpha = 0.025 per side) is run and reported
  for the headline and subgroups even though it will almost certainly fail; verdict wording
  as fixed in preregistration Section 11.

## Possible robustness checks (not preregistered, not implemented)

- Employment-weighted aggregation of exposure across O*NET-SOC variants and SOC targets,
  instead of unweighted means. Would need a deviation entry if adopted.

## Open `[verify]` items carried forward

- OCC2010 coverage across the 2020 code change: harmonised codes exist; the empirical
  coverage report is due in Phase 4
- Teleworkability data source
- HonestDiD availability in Python

## Working agreement

- One phase step per exchange, at most five actions per message
- Code arrives either as a complete file or with exact line numbers
- Concepts are explained before code
- Every step ends with a commit and a push
- Null and mixed results are reported as clearly as positive ones
