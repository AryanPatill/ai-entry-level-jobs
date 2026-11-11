"""Rules significance, quintile, number_required, and reviewer rule 4 (Aryan 2026-11-11).

The rejected texts are the accepted-but-wrong claims from results/tables/phase11_traces/ (2026-11-11)."""
import pytest

from src.agents.registry import REGISTRY_DIR
from src.agents.schemas import Claim
from src.agents.skeptic import check

pytestmark = pytest.mark.skipif(not (REGISTRY_DIR / "phase8_main.json").exists(), reason="registry not built")
T = "phase8_main.terms."
L3 = "phase8_main.l3_within_age_q5_vs_q1."


def rules(text, refs=(), **kw):
    return {i.rule for i in check(Claim(text, "DESCRIPTIVE", tuple(refs)), **kw).issues}


def test_significance_beside_a_value_must_match_its_p():
    # gradient on qwen3:4b: Q3's p is 0.266
    bad = "-5.4% change for ages 22-25 in AI-exposed occupations is 0.266 statistically significant."
    assert "significance" in rules(bad, [T + "q3_a22.pct", T + "q3_a22.p"])
    good = "-5.4% change for ages 22-25 in Q3 is not statistically significant (0.266), relative to ages 35-49."
    assert "significance" not in rules(good, [T + "q3_a22.pct", T + "q3_a22.p"])


def test_significance_on_quintile_labels_must_match_each_quintile():
    # gradient on qwen3:8b: Q2's p is 0.021, so "no significant difference in Q2" is wrong
    bad = "For ages 22-25, Q4 shows a -17.2% change, but no significant difference in Q2 and Q3."
    assert "significance" in rules(bad, [T + "q4_a22.pct"])
    good = "For ages 22-25, Q4 shows a -17.2% change, but no significant difference in Q3."
    assert "significance" not in rules(good, [T + "q4_a22.pct"])


def test_quintile_label_must_match_the_value():
    # gradient on qwen3:8b: the Q2 estimate attached to Q5
    bad = "For ages 22-25, employment in AI-exposed occupations (Q5) relative to Q1 shows a -9.4% change."
    assert "quintile" in rules(bad, [T + "q2_a22.pct"])
    good = "For ages 22-25, employment in Q2 occupations relative to Q1 shows a -9.4% change."
    assert "quintile" not in rules(good, [T + "q2_a22.pct"])


def test_accepted_comparison_group_wording_passes_significance():
    text = ("Within ages 22-25, the change is -5.1%, with a 95% CI from -16.3% to +7.5%, and this change is not "
            "statistically significant (0.412). In contrast, within ages 35-49, the change was +14.0%, and this "
            "change is statistically significant (0.008).")
    refs = [L3 + "22-25.pct", L3 + "22-25.lo", L3 + "22-25.hi", L3 + "22-25.p", L3 + "35-49.pct", L3 + "35-49.p"]
    assert "significance" not in rules(text, refs)


def test_number_required_only_when_asked():
    assert "number_required" in rules("The headline is relative. Say so.", require_number=True)
    assert "number_required" not in rules("The headline is relative. Say so.")


def test_reviewer_cannot_object_to_a_verified_significance_statement():
    from src.agents.pipeline import Finding, grounded
    c = Claim("Within ages 22-25 the change is -5.1%, which is not statistically significant, and the wording is final.",
              "DESCRIPTIVE", (L3 + "22-25.pct",))
    kept = grounded(c, [Finding(quote="which is not statistically significant", problem="overstates certainty"),
                        Finding(quote="the wording is final", problem="overstates certainty")])
    assert [i.quote for i in kept] == ["the wording is final"]


def test_rendered_value_at_the_rounding_boundary_is_reported():
    # tech_finance, 2026-11-11: registry -17.55 renders as -17.6%; the number rule must accept it.
    from src.agents.writer import WriterDraft, render
    key = "phase9_robustness.checks.T1(a) drop tech and finance (sectors 1, 2).lo"
    c = render(WriterDraft(template="the lower bound is {" + key + "}", label="DESCRIPTIVE"))
    assert "-17.6%" in c.text and "number" not in {i.rule for i in check(c).issues}


def test_metadata_is_not_citable():
    from src.agents.writer import keys_for
    keys = keys_for("phase9_robustness.checks.Placebo group", "phase9_randomization_inference.")
    assert keys and not any(k.rsplit(".", 1)[-1] in {"section", "kind", "seed"} for k in keys)


def test_number_required_has_a_requirement_line():
    from src.agents.writer import feedback_text
    assert "REQUIRED" in feedback_text(["number_required: a write-up claim ... must cite at least one"])


def test_reviewer_cannot_object_to_the_required_comparison_wording():
    from src.agents.pipeline import Finding, grounded
    c = Claim("For ages 22-25 in Q2, the estimate is -9.4%, compared to ages 35-49 and Q1, a dramatic collapse.",
              "DESCRIPTIVE", ("phase8_main.terms.q2_a22.pct",))
    kept = grounded(c, [Finding(quote="compared to ages 35-49 and Q1", problem="overstates certainty"),
                        Finding(quote="a dramatic collapse", problem="overstates")])
    assert [i.quote for i in kept] == ["a dramatic collapse"]


def test_rendering_integers_booleans_and_label_prefix():
    from src.agents.writer import WriterDraft, fmt, render
    assert fmt("phase9_randomization_inference.n_shuffles", 1000) == "1000"
    assert fmt("x.seed", 20261104) == "20261104"
    assert fmt("phase8_main.pretrend.flagged", False) == "no"
    c = render(WriterDraft(template="The DESCRIPTIVE sentence is: the shuffles were {phase9_randomization_inference.n_shuffles}.",
                           label="DESCRIPTIVE"))
    assert c.text == "the shuffles were 1000."
