# Plan

Phase status and current position. Updated at the end of every step, before the commit.
Phase detail lives in `preregistration.md` (design) and `architecture.md` (mechanics).

## Where the project stands

- **Current phase:** 11, agent layer
- **Last completed step:** Phase 5 done (student filter: ages 22-25 only, 2026-10-17)
- **Next step:** Aryan installs Ollama and pulls qwen2.5:7b and llama3.2:3b; then the live 11.5 demo, then 11.6

## Phases

| Phase | Name | Main output | Status |
|---|---|---|---|
| 0 | Setup questions | Environment recorded | Done |
| 1 | Research design | `preregistration.md` v1.0 | Done |
| 2 | Environment | Repo, venv, git, config | Done |
| 3 | Data acquisition | Raw Parquet, sector map, data dictionary | Done |
| 4 | Crosswalks and exposure mapping | Exposure-mapped occupations, coverage report | Done |
| 5 | Cleaning and sample construction | Analysis panel | Done |
| 6 | EDA and descriptive replication | Trend figures, descriptive comparison | Done |
| 7 | Identification strategy | Causal diagram, assumptions, threats-to-tests table | Done |
| 8 | Estimation | DiD, triple-difference, event-study tables | Done |
| 9 | Robustness and falsification | Placebo, sensitivity, inference tables | Done; HonestDiD and alternative exposure measures logged as deviations |
| 10 | Heterogeneity | Subgroup results | Done |
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
| 6 | Student-filter column `emp_w_student`, window 2013-01+ (age scope: Aryan) | Done |

## Phase 6 steps (approved by Aryan 2026-10-17: base bin -1, 2015 onward, subgroups in Phase 10, stop after each stage)

Every figure and table is titled DESCRIPTIVE; no causal language, no model estimation (Phase 8).
Weighted counts (`emp_w`), main-sample months, grouped into the Section 9 quarterly bins;
pandemic months shown as a gap. Stops for review after each stage.

| Step | What | Reveals outcome trends? | Status |
|---|---|---|---|
| A1 | Records per month, all groups pooled; 2025-10 gap and 2025-11 low response flagged | No | Done |
| A2 | Threat 6: Dec 2019 vs Jan 2020 employment per occupation, all ages pooled; flag large jumps | One month boundary per occupation; no age or quintile trend | Done |
| A3 | "Hours vary" share by quintile x period (commitment) | No (a measurement variable, not an outcome) | Done |
| B1 | Employment by age group over time, quintiles pooled | Yes: age trends only | Done |
| B2 | Employment by quintile over time, ages pooled | Yes: exposure trends only | Done |
| C1 | Employment index by quintile, ages 22-25 (the payroll-paper figure) | Yes: first age x exposure view | Done |
| C2 | Same index for 26-34, 35-49, 50-64 | Yes | Done |
| C3 | Unadjusted triple-difference ratio over time: (Q5/Q1 at 22-25) / (Q5/Q1 at 35-49) | Yes: closest to the headline | Done |
| C4 | Exploratory occupation-share outcome (Section 6) | Yes | Done |
| D1 | Unemployment rate by quintile x age group | Yes | Done |
| D2 | Mean hours by quintile x age group (read with A3) | Yes | Done |
| E1 | Descriptive comparison with the payroll paper: C1/C3 change since 2022 vs 13-19% | Yes: a headline-like number, labelled DESCRIPTIVE | Done |

## Phase 7 steps (approved 2026-11-03: growth window 2015-01 to 2020-02, occupation x sector panel, data-learned checks exploratory)

Output: `docs/identification.md` (new; index.md gets a row). Design changes, if any, go to
deviations.md; new checks are labelled exploratory (Section 10) unless Aryan rules otherwise.

| Step | What | Touches outcomes? | Status |
|---|---|---|---|
| 7.1 | Estimand and identifying assumption restated in panel notation; what each fixed effect absorbs and what it cannot | No | Done |
| 7.2 | Causal diagram (Mermaid, renders on GitHub): AI exposure, age, time, and every threat path from Section 12 | No | Done |
| 7.3 | Threats-to-tests table: Section 12's seven threats, each with mechanism, why the fixed effects do or do not absorb it, the test, data needed, status | No | Done |
| 7.4 | Data-learned threats added to the table (exploratory): age-differential 2020 code breaks; 2025 weight revision and Q2 shift; comparison-group (35-49 Q5) movement; shrinking sample | No | Done |
| 7.5 | Resolve `[verify]`s: teleworkability source (threat 3), HonestDiD in Python (Section 13), field of degree absent from CPS (threat 4) | No (source checks only; any download asks first) | Done (T3 download pending Aryan) |
| 7.6 | Pre-specify definitions Section 12 leaves open: threat-2 growth control window; threat-1 industry x age x month built from the sector map | 7.6a computes pre-period occupation growth, a pre-period outcome | Done |

## Phase 11 steps (agent layer; started 2026-11-09)

The LLM layer never produces numbers (decisions 2026-09-16). Everything an agent says is checked
against the registry before it leaves the pipeline.

| Step | What | Needs | Status |
|---|---|---|---|
| 11.1 | Results registry: analysis modules write results/registry/*.json; `src/agents/registry.py` flattens them | Nothing new | Done |
| 11.2 | Typed handoffs: `Claim`, `Issue`, `SkepticReport`, `MapperResult` (stdlib dataclasses) | Nothing new | Done |
| 11.3 | Skeptic, rule-based: label, numbers, causal wording, verdict, comparison caveat | Nothing new | Done |
| 11.4 | Mapper, baseline: job title -> OCC2010 by string similarity | Nothing new | Done |
| 11.5 | LangGraph pipeline: Writer (LLM drafts templates) -> render (code fills registry numbers) -> Skeptic (rules, then LLM review) -> revise loop, max 3; LLM Mapper choosing among baseline candidates | LangGraph (installed); Ollama with qwen2.5:7b | Built and tested with scripted stand-ins; live run blocked until Ollama is installed |
| 11.6 | Wire the pipeline to produce the write-up's claims; every published sentence passes the Skeptic | 11.5 | Not started |

## Phase 12 steps (agent evaluation; planned)

| Step | What | Status |
|---|---|---|
| 12.1 | Skeptic catch rate: grow the seed set (tests/test_agents.py) to about 50 bad and 25 good claims; report catch rate and false-alarm rate, rules alone and rules + LLM | Not started |
| 12.2 | Mapper accuracy: about 100 job titles hand-coded to OCC2010; top-1 and top-3 accuracy, baseline vs LLM | Not started |

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

## Working agreement

- One phase step per exchange, at most five actions per message
- Code arrives either as a complete file or with exact line numbers
- Concepts are explained before code
- Every step ends with a commit and a push
- Null and mixed results are reported as clearly as positive ones
