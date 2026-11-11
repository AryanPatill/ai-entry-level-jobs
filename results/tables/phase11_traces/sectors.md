# Trace: sectors

Model `qwen3:8b`, seed 20261111; rule set 8988660c47e4b17d; status **rejected** after 4 draft(s). Agent output, not analysis.

Topic: The exploratory sector estimates for finance and for information and professional services.

## Draft 1

Template (model output):

> In the exploratory sector estimates, young workers (ages 22-25) in Information and professional/technical services experienced a {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct} percentage point decline in employment compared to ages 35-49 and the least exposed quintile (Q1), with a 95% confidence interval ranging from {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.lo} to {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.hi}, and a p-value of {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.p}. In Finance, insurance, and real estate, the decline was {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.pct} percentage points, with a confidence interval from {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.lo} to {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.hi}, and a p-value of {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.p}.

Rendered claim:

> In the exploratory sector estimates, young workers (ages 22-25) in Information and professional/technical services experienced a -29.2% percentage point decline in employment compared to ages 35-49 and the least exposed quintile (Q1), with a 95% confidence interval ranging from -52.2% to +4.8%, and a p-value of 0.085. In Finance, insurance, and real estate, the decline was -47.0% percentage points, with a confidence interval from -66.5% to -16.1%, and a p-value of 0.007.

- **units**: a percent change in employment is called 'percentage points'. Triggered by: "percentage point".

## Draft 2

Template (model output):

> DESCRIPTIVE: In {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct} percent of {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.p} probability, the employment of young workers (ages 22-25) in Information and professional/technical services is {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct} percent relative to ages 35-49 and the least exposed quintile (Q1), with a confidence interval ranging from {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.lo} to {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.hi} percent.

Rendered claim:

> DESCRIPTIVE: In -29.2% of 0.085 probability, the employment of young workers (ages 22-25) in Information and professional/technical services is -29.2% relative to ages 35-49 and the least exposed quintile (Q1), with a confidence interval ranging from -52.2% to +4.8%.

- **repeat**: renders the same registry value more than once. Triggered by: "phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct".

## Draft 3

Template (model output):

> In the exploratory sector estimates, {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct} percentage point decline in employment for young workers (ages 22-25) in AI-exposed occupations within the Information and professional/technical services sector relative to ages 35-49 and the least exposed quintile (Q1), with a confidence interval ranging from {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.lo} to {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.hi}, and a p-value of {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.p}. In the Finance, insurance, and real estate sector, a {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.pct} percentage point decline was observed, with a confidence interval from {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.lo} to {phase0_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.hi}, and a p-value of {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.p}.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['phase0_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.hi']. Triggered by: absence (nothing to quote).

## Draft 4

Template (model output):

> In the exploratory sector estimates, {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.pct} percent of young workers in {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.q2} experienced employment changes relative to {phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.q1}, while {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.pct} percent of young workers in {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.q2} showed similar changes relative to {phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.q1}.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.q2', 'phase10_heterogeneity.sectors_exploratory.Information and professional/technical services.q1', 'phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.q2', 'phase10_heterogeneity.sectors_exploratory.Finance, insurance, and real estate.q1']. Triggered by: absence (nothing to quote).
