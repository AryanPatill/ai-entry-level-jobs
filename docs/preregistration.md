# Preregistration: Is AI Really Taking Entry-Level Jobs?

- **Author:** Aryan Patil
- **Version:** 1.0
- **Written:** 2026-09-17
- **Status:** Written before any data was downloaded or any outcome was viewed.
- **Rule:** Any change after this version is logged in `docs/deviations.md` with the date and reason.

---

## 1. Research question

Since late 2022, when generative AI chat tools became widely available, have employment
outcomes for young workers (ages 22–25) in AI-exposed occupations declined relative to:

- (a) young workers in less-exposed occupations, and
- (b) older workers (ages 35–49) in the same occupations?

## 2. Estimand

The change in employment of 22–25-year-olds in the most AI-exposed occupations (Q5),
after December 2022, beyond the change for:

- 22–25-year-olds in the least-exposed occupations (Q1), and
- 35–49-year-olds in those same Q5 occupations.

This is a triple difference (exposure × age × post). A non-zero estimate is interpreted as
causal only under the assumptions in Section 11 and only if the tests in Section 12 do not
overturn it. Otherwise it is reported as descriptive.

## 3. Data

| Item | Choice |
|---|---|
| Source | IPUMS CPS, monthly basic samples |
| Main start | January 2015 |
| Robustness start | January 2011 |
| End | Latest month available at data pull. Recorded here on pull date: ____________ |
| Excluded months (main) | March 2020 – December 2021 |
| Microdata | Never committed to git; IPUMS citation included in all outputs |

## 4. Sample

| Item | Main | Robustness |
|---|---|---|
| Treated age group | 22–25 | — |
| Secondary age group | 26–34 (reported as a step-pattern check, not a standalone finding) | — |
| Comparison age group | 35–49 | — |
| Education | All levels | Bachelor's or higher (subgroup, Section 14; filter applied to all age groups) |
| Class of worker | All wage and salary employees (private and government) | Private-sector employees only |
| Students | No enrollment filter | Full-time workers only (35+ usual hours); enrolled 22–24-year-olds dropped only if the enrollment variable covers all ages 22–25 [verify] |
| Employed but absent | Counted as employed | — |

## 5. Occupations and exposure

- **Occupation code:** IPUMS harmonized `OCC2010`, consistent across the January 2020 code
  change. Coverage for 2020 onward to be checked in Phase 3 [verify].
- **Primary exposure measure:** Eloundou et al. (2023/2024), GPT-4 β score [verify exact column name].
- **Robustness measures:** Felten et al. AIOE (LLM version if available); Anthropic Economic Index
  (labeled post-treatment, because it is measured after December 2022).
- **Mapping:** `OCC2010` → SOC → O*NET-SOC, with a coverage report (share of employment matched,
  every unmatched occupation explained). Built in Phase 4.
- **Quintiles:** employment-weighted, so each quintile holds about 20% of workers.
  Cutoffs fixed on employment of wage and salary workers ages 22–64, January 2015 – February 2020.
  Cutoffs are never recomputed with post-treatment data.

## 6. Outcomes

| Role | Outcome | Model |
|---|---|---|
| Primary | Weighted employment count (sum of `WTFINL`) per occupation × age group × month | Poisson, Section 8 |
| Secondary | Unemployment rate per cell (unemployed are placed by last occupation; people with no occupation are excluded [verify]) | Weighted linear regression, same fixed effects, weighted by cell population |
| Secondary | Mean usual weekly hours at main job among the employed [verify variable] | Weighted linear regression, same fixed effects, weighted by cell employment |
| Exploratory | Occupation share: of all employed 22–25-year-olds, the share in each quintile | Reported regardless of result |

## 7. Treatment timing

| Role | Date | Reason |
|---|---|---|
| Main | December 2022 | First CPS reference week after ChatGPT's public release (30 Nov 2022) |
| Alternative | March 2023 | Allows for early business adoption |
| Alternative | January 2024 | Allows a full year for adoption |

`Post_t = 1` for all months from the treatment date onward.

## 8. Main model

Unit: occupation (o) × age group (a) × month (t).

    E[Y_oat] = exp( SUM over q in {2,3,4,5} and a in {22-25, 26-34} of
                        beta_qa * 1[Q_o = q] * 1[age = a] * Post_t
                    + alpha_oa + gamma_ot + delta_at )

- `Y_oat`: weighted employment count
- `alpha_oa`: occupation × age fixed effects
- `gamma_ot`: occupation × month fixed effects
- `delta_at`: age × month fixed effects
- Reference groups: Q1 and ages 35–49
- **Headline estimate:** `beta_(5, 22-25)`, reported as a percentage change `exp(beta) − 1`
- Estimated with Poisson pseudo-maximum likelihood (pyfixest `fepois` [verify support for this setup])
- Survey weights enter through the outcome (weighted counts)

## 9. Event study

- Same model, with `Post_t` replaced by quarterly bin indicators counted from December 2022.
- Bin 0 = Dec 2022 – Feb 2023; bin −1 = Sep – Nov 2022; bin +1 = Mar – May 2023; and so on.
- **Main reference bin:** Sep – Nov 2022 (bin −1).
- **Robustness reference bin:** Dec 2019 – Feb 2020.
- Bins overlapping excluded months use only the remaining months.
- **Headline plot:** Q5 × ages 22–25, all bins, with 95% confidence intervals.

## 10. Inference

- Standard errors clustered by occupation (`OCC2010`).
- Wild cluster bootstrap only for models with fewer than 50 clusters. If Poisson is not supported,
  a linear version is used for that check and logged as a deviation.
- Randomization inference on the headline: 1,000 shuffles of exposure scores across occupations
  (fewer if too slow; logged).

### Multiple testing

| Family | Tests | Correction |
|---|---|---|
| Headline | `beta_(5, 22-25)` | None (single preregistered test) |
| Secondary outcomes | Unemployment rate, hours | Holm, within family |
| Subgroups | Bachelor's or higher, men, women | Holm, within family |
| Exploratory and robustness | Everything else | None; always labeled |

## 11. Decision rules

### "No meaningful effect" rule (headline and subgroups)

Threshold: ±5% (in coefficient terms, ln(0.95) = −0.0513 to ln(1.05) = 0.0488).

| 95% CI, in percent terms | Verdict |
|---|---|
| Entirely below −5% or entirely above +5% | Effect found |
| Entirely within −5% to +5% | No meaningful effect |
| Anything else | Inconclusive |

### Pre-trend rule

A pre-trend is flagged if **either**:

- the joint test that all pre-period bin coefficients (Q5 × ages 22–25) equal zero has p < 0.05, or
- any single pre-period bin's 95% CI lies entirely beyond ±5%.

If flagged, the main result is reported with a clear warning, and the sensitivity analysis
(Section 13) becomes the main basis for interpretation.

### Identifying assumption

Without AI, the Q5-vs-Q1 employment gap for 22–25-year-olds would have changed the same way
as the gap for 35–49-year-olds. The fixed effects remove shocks common to an occupation-month,
an age-month, or an occupation-age pair. Only shocks hitting young workers more than older
workers in exposed occupations after December 2022 can bias the estimate.

## 12. Threats and tests

| # | Threat | Test | Strength |
|---|---|---|---|
| 1 | Rate hikes cut junior hiring more in tech and finance | (a) Drop tech and finance industries; (b) add industry × age × month fixed effects | Good |
| 2 | Post-pandemic over-hiring correction | Control: occupation pre-treatment growth × age × post; inspect 2022 event-study bins | Good |
| 3 | Remote work makes juniors harder to train | Control: occupation teleworkability (Dingel & Neiman 2020 [verify]) × age × post | Good, if available |
| 4 | More young people studied CS, data, and business | (a) Event-study pre-trends; (b) drop computer and math occupations. Field of degree not in CPS [verify] | Partial; reported as a limitation |
| 5 | Uneven pandemic recovery in 2022 | Pre-pandemic reference bin; pandemic months kept with controls | Good |
| 6 | January 2020 occupation code change | Phase 4 coverage report; compare Dec 2019 vs Jan 2020 employment by occupation and flag large jumps | Good |
| 7 | Design finds effects where none exist | Placebo dates Dec 2017 and Dec 2018, using Jan 2015 – Feb 2020 only | Good |

Controls in threats 1–3 may absorb part of a real AI effect. A shrinking estimate under these
tests means "cannot separate AI from this threat," not "AI had no effect."

**Placebo group:** the same model with ages 50–64 in place of 22–25, compared with 35–49.
A clear "effect" there is a warning sign.

## 13. Robustness checks

- Alternative treatment dates: March 2023, January 2024
- Start in January 2011
- Pandemic months kept, with quintile × age × pandemic-period indicators
- Alternative exposure measures (Section 5)
- Continuous exposure score instead of quintiles
- Private-sector employees only
- Full-time workers only (also the closest comparison to the Stanford ADP sample)
- Student filter (only if supported)
- Unweighted counts
- Basic fixed effects (occupation, age, month separately, plus two-way terms)
- Pre-pandemic reference bin
- Sensitivity to parallel-trend violations (Rambachan & Roth "HonestDiD" approach) in Phase 9;
  logged as a deviation if no reliable Python tool exists [verify]

## 14. Subgroups (Holm-corrected family)

- Bachelor's degree or higher (all age groups filtered)
- Men
- Women

Same ±5% three-verdict rule.

## 15. Exploratory analyses (uncorrected, always labeled)

- Occupation share outcome (Section 6)
- Broad industry sectors: (1) information and professional/technical services,
  (2) finance, insurance, and real estate, (3) manufacturing, (4) wholesale and retail trade,
  (5) education, health, and social services, (6) all other. Code ranges mapped from the IPUMS
  industry codebook in Phase 3, before any outcome analysis.
- Automation vs augmentation exposure, only if the data supports it; otherwise logged as a deviation.

## 16. Planned checks before estimation

- **Cell-size counts** (people only, no outcome trends), right after Phase 3.
- **Minimum detectable effect** for the headline, using pre-period data only, at the end of Phase 5.

## 17. Reporting commitments

- The headline verdict is reported whatever it is: effect, no meaningful effect, or inconclusive.
- Every result is labeled **descriptive** or **causal (under stated assumptions)**.
- All preregistered tests are reported, including ones that weaken the headline.
- The agent layer (Phase 11) never produces numbers; all numbers come from code.

## 18. Background literature (checked 2026-09-17)

- **Brynjolfsson, Chandar & Chen, "Canaries in the Coal Mine?"** (Stanford Digital Economy Lab,
  Aug 2026 version). ADP payroll data through June 2026. Employment of 22–25-year-olds in
  AI-exposed occupations about 19% below the trend of less-exposed peers; no comparable gap for
  experienced workers; no economy-wide displacement; works mainly through reduced hiring.
  Earlier versions: 13% (Aug 2025), 16% with firm-level controls (Nov 2025). Framed as
  "consistent with" AI impact. Main sample: full-time workers.
  https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/
- **Deming** (Harvard): argues junior hiring began declining about six months before ChatGPT and
  points to remote work. NPR, Aug 2026.
  https://www.npr.org/2026/08/18/nx-s1-5910677/recent-college-graduates-employment-job-artificial-intelligence
- **Humlum & Vestergaard, "Large Language Models, Small Labor Market Effects"** (BFI/NBER).
  Danish administrative data; precise null effects on earnings and hours, ruling out effects
  larger than 2% two years after, including early-career jobs.
  https://bfi.uchicago.edu/working-papers/large-language-models-small-labor-market-effects/
- **IPUMS CPS OCC2010 documentation:** https://cps.ipums.org/cps-action/variables/418412

## 19. Change log

| Date | Version | Change |
|---|---|---|
| 2026-09-17 | 1.0 | Initial preregistration |