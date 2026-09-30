# Plan

Phase status and current position. Updated at the end of every step, before the commit.
Phase detail lives in `preregistration.md` (design) and `architecture.md` (mechanics).

## Where the project stands

- **Current phase:** 3, data acquisition
- **Last completed step:** 4b, IND1990 mapped to the six preregistered sectors
- **Next step:** Phase 3, final step: the data dictionary (`data_dictionary.md`)

## Phases

| Phase | Name | Main output | Status |
|---|---|---|---|
| 0 | Setup questions | Environment recorded | Done |
| 1 | Research design | `preregistration.md` v1.0 | Done |
| 2 | Environment | Repo, venv, git, config | Done |
| 3 | Data acquisition | Raw Parquet, sector map, data dictionary | In progress |
| 4 | Crosswalks and exposure mapping | Exposure-mapped occupations, coverage report | Not started |
| 5 | Cleaning and sample construction | Analysis panel | Not started |
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
| 5 | Data dictionary | Not started |

## Open `[verify]` items carried forward

- OCC2010 coverage across the 2020 code change: harmonised codes exist; the empirical
  coverage report is due in Phase 4
- pyfixest Poisson with three-way fixed effects and weights
- Eloundou exposure file: column names and occupation code system
- Teleworkability data source
- HonestDiD availability in Python

## Working agreement

- One phase step per exchange, at most five actions per message
- Code arrives either as a complete file or with exact line numbers
- Concepts are explained before code
- Every step ends with a commit and a push
- Null and mixed results are reported as clearly as positive ones
