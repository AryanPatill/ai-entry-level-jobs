# Trace: subgroups

Model `qwen3:8b`, seed 20261111; rule set 8988660c47e4b17d; status **accepted** after 2 draft(s). Agent output, not analysis.

Topic: The subgroup estimates for men, women and bachelor's-or-higher, with Holm-adjusted p-values and verdicts.

## Draft 1

Template (model output):

> The {phase10_heterogeneity.subgroups.Bachelor's or higher.pct} percentage point decline in employment among young workers with a bachelor's or higher degree in AI-exposed occupations is {phase10_heterogeneity.subgroups.Bachelor's or higher.verdict}, relative to ages 35-49 and the least exposed quintile (Q1).

Rendered claim:

> The -16.3% percentage point decline in employment among young workers with a bachelor's or higher degree in AI-exposed occupations is Inconclusive, relative to ages 35-49 and the least exposed quintile (Q1).

- **units**: a percent change in employment is called 'percentage points'. Triggered by: "percentage point".

## Draft 2

Template (model output):

> The DESCRIPTIVE sentence is: For Bachelor's or higher, the employment rate in AI-exposed occupations among young workers (ages 22-25) was {phase10_heterogeneity.subgroups.Bachelor's or higher.pct} percent relative to ages 35-49 and the least exposed quintile (Q1), with a 95% confidence interval ranging from {phase10_heterogeneity.subgroups.Bachelor's or higher.lo} to {phase10_heterogeneity.subgroups.Bachelor's or higher.hi}, and a Holm-adjusted p-value of {phase10_heterogeneity.subgroups.Bachelor's or higher.holm_p}, leading to a verdict of {phase10_heterogeneity.subgroups.Bachelor's or higher.verdict}.

Rendered claim:

> The DESCRIPTIVE sentence is: For Bachelor's or higher, the employment rate in AI-exposed occupations among young workers (ages 22-25) was -16.3% relative to ages 35-49 and the least exposed quintile (Q1), with a 95% confidence interval ranging from -28.6% to -1.8%, and a Holm-adjusted p-value of 0.058, leading to a verdict of Inconclusive.

Rules fired: none (passed).

