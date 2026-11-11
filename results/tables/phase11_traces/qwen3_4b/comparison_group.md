# Trace: comparison_group

Model `qwen3:4b`; rule set f4286cc46e4d2d2e; status **rejected** after 4 draft(s). Agent output, not analysis.

Topic: How the two within-age comparisons differ: Q5 vs Q1 within ages 22-25 and within ages 35-49.

## Draft 1

Template (model output):

> DESCRIBED: The {key1} for ages 22-25 shows a {key2} change from Q1 to Q5, while the {key3} for ages 35-49 shows a {key4} change from Q1 to Q5. The {key5} for ages 22-25 is not statistically significant.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['key1', 'key2', 'key3', 'key4', 'key5']. Triggered by: absence (nothing to quote).

## Draft 2

Template (model output):

> The {phase8_main.l3_within_age_q5_vs_q1.22-25.pct} change in {phase8_main.l3_within_age_q5_vs_q1.22-25.pct} for young workers (ages 22-25) compared to least exposed occupations is {phase8_main.l3_within_age_q5_vs_q1.22-25.lo} to {phase8_main.l3_within_age_q5_vs_q1.22-25.hi} and not statistically significant, while the {phase8_main.l3_within_age_q5_vs_q1.35-49.pct} change for older workers (ages 35-49) is {phase8_main.l3_within_age_q5_vs_q1.35-49.lo} to {phase8_main.l3_within_age_q5_vs_q1.35-49.hi} and statistically significant.

Rendered claim:

> The -5.1% change in -5.1% for young workers (ages 22-25) compared to least exposed occupations is -16.3% to +7.5% and not statistically significant, while the +14.0% change for older workers (ages 35-49) is +3.4% to +25.7% and statistically significant.

- **repeat**: renders the same registry value more than once. Triggered by: "phase8_main.l3_within_age_q5_vs_q1.22-25.pct".

## Draft 3

Template (model output):

> The headline shows that in {age_group} occupations, young workers (ages 22-25) experienced a {change} change in exposure to AI tasks compared to least exposed occupations, with the difference being {statistical_significance}.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['age_group', 'change', 'statistical_significance']. Triggered by: absence (nothing to quote).

## Draft 4

Template (model output):

> The {phase8_main.l3_within_age_q5_vs_q1.22-25.pct} change in {age_group} for {phase8_main.l3_within_age_q5_vs_q1.22-25.pct} is {statistical_significance} for {phase8_main.l3_within_age_q5_vs_q1.22-25.pct} and {phase8_main.l3_within_age_q5_vs_q1.35-49.pct} for {age_group}.

Rendered claim:

> (not rendered: template rejected)

- **structure**: unknown registry keys: ['age_group', 'statistical_significance', 'age_group']. Triggered by: absence (nothing to quote).
