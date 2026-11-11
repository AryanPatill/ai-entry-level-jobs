# Trace: tech_finance

Model `qwen3:8b`, seed 20261111; rule set 8988660c47e4b17d; status **rejected** after 4 draft(s). Agent output, not analysis.

Topic: How the headline changes when tech and finance are dropped and with industry x age x month fixed effects.

## Draft 1

Template (model output):

> DESCRIPTIVE: In {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).section}, the percentage change in employment for young workers (ages 22-25) in AI-exposed occupations relative to ages 35-49 and the least exposed quintile (Q1) is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).pct}, with a confidence interval ranging from {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).lo} to {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).hi}. The result is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).reading}, and the effect size is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).ratio_to_main} times the main estimate. In {phase9_robustness.checks.T1(b) industry x age x month fixed effects.section}, the percentage change is {phase9_robustness.checks.T1(b) industry x age x month fixed effects.pct}, with a confidence interval from {phase9_robustness.checks.T1(b) industry x age x month fixed effects.lo} to {phase9_robustness.checks.T1(b) industry x age x month fixed effects.hi}, and the result is {phase9_robustness.checks.T1(b) industry x age x month fixed effects.reading}, with an effect size of {phase9_robustness.checks.T1(b) industry x age x month fixed effects.ratio_to_main} times the main estimate.

Rendered claim:

> DESCRIPTIVE: In 12, the percentage change in employment for young workers (ages 22-25) in AI-exposed occupations relative to ages 35-49 and the least exposed quintile (Q1) is -10.1%, with a confidence interval ranging from -17.6% to -1.9%. The result is Inconclusive, and the effect size is 0.7 times the main estimate. In 12, the percentage change is -12.2%, with a confidence interval from -19.9% to -3.9%, and the result is Inconclusive, with an effect size of 0.86 times the main estimate.

- **number**: 12 is not a reported number. Triggered by: "12".
- **number**: 17.6 is not a reported number. Triggered by: "17.6".
- **number**: 12 is not a reported number. Triggered by: "12".

## Draft 2

Template (model output):

> DESCRIPTIVE: When tech and finance sectors are dropped, the estimated effect of AI exposure on employment for young workers (ages 22-25) in AI-exposed occupations is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).pct}, with a confidence interval ranging from {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).lo} to {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).hi}. This estimate is relative to ages 35-49 and the least exposed quintile (Q1). When industry x age x month fixed effects are included, the estimate is {phase9_robustness.checks.T1(b) industry x age x month fixed effects.pct}, with a confidence interval from {phase9_robustness.checks.T1(b) industry x age x month fixed effects.lo} to {phase9_robustsness.checks.T1(b) industry x age x month fixed effects.hi}.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['phase9_robustsness.checks.T1(b) industry x age x month fixed effects.hi']. Triggered by: absence (nothing to quote).

## Draft 3

Template (model output):

> DESCRIPTIVE: {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).pct} {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).lo} to {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).hi} for ages 22-25 in AI-exposed occupations, relative to ages 35-49 and Q1, with {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).p} significance.

Rendered claim:

> DESCRIPTIVE: -10.1% -17.6% to -1.9% for ages 22-25 in AI-exposed occupations, relative to ages 35-49 and Q1, with 0.017 significance.

- **number**: 17.6 is not a reported number. Triggered by: "17.6".

## Draft 4

Template (model output):

> DESCRIPTIVE: When tech and finance sectors are dropped, the estimated effect on employment of young workers (ages 22-25) in AI-exposed occupations relative to ages 35-49 and the least exposed quintile (Q1) is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).pct}, with a 95% confidence interval ranging from {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).lo} to {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).hi}. The result is statistically significant at the 5% level ({phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).p}), and the effect size is {phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).ratio_to_main} times the main estimate. When industry x age x month fixed effects are included, the estimated effect is {phase9_robustness.checks.T1(b) industry x age x month fixed effects.pct}, with a 95% confidence interval from {phase9_robustness.checks.T1(b) industry x age x month fixed effects.lo} to {phase9_robustsness.checks.T1(b) industry x age x month fixed effects.hi}, and is statistically significant at the 1% level ({phase9_robustness.checks.T1(b) industry x age x month fixed effects.p}).

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['phase9_robustsness.checks.T1(b) industry x age x month fixed effects.hi']. Triggered by: absence (nothing to quote).
