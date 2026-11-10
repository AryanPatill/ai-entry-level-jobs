"""Phase 11 agent layer: the rule-based Skeptic and the baseline Mapper.

The Skeptic cases are also the seed of the Phase 12 evaluation set (catch rate)."""
import pytest

from src.agents.registry import REGISTRY_DIR
from src.agents.schemas import Claim
from src.agents.skeptic import check, numbers_in

needs_registry = pytest.mark.skipif(not (REGISTRY_DIR / "phase8_main.json").exists(), reason="registry not built")

GOOD = [
    Claim("DESCRIPTIVE: employment of 22-25-year-olds in Q5 occupations changed by 14.1% relative to Q1 and "
          "to ages 35-49 after 2022-12 (95% CI 21.5% to 6.0%); headline verdict: effect detected.", "DESCRIPTIVE"),
    Claim("Placebo dates in 2017 and 2018 give +2.5% and -0.7%.", "DESCRIPTIVE"),
]
BAD = [  # (claim, rule that must fire)
    (Claim("Employment of young workers in exposed jobs fell 19% relative to ages 35-49.", "DESCRIPTIVE"), "number"),
    (Claim("AI caused a 14.1% drop relative to 35-49-year-olds.", "DESCRIPTIVE"), "causal"),
    (Claim("This proves AI is taking entry-level jobs.", "CAUSAL_UNDER_ASSUMPTIONS"), "causal"),
    (Claim("Young workers in Q5 jobs lost 14.1% of employment.", "DESCRIPTIVE"), "caveat"),
    (Claim("The Q5 headline is inconclusive, relative to 35-49.", "DESCRIPTIVE"), "verdict"),
    (Claim("Employment of 22-25 in Q5 fell relative to 35-49.", "FINDING"), "label"),
]


def test_numbers_skip_ages_years_and_quintiles():
    assert numbers_in("22-25 in Q5 since 2022-12, Section 11: 14.1% and 0.98") == [14.1, 0.98]


@needs_registry
@pytest.mark.parametrize("claim", GOOD)
def test_good_claims_pass(claim):
    rep = check(claim)
    assert rep.passed, rep.issues


@needs_registry
@pytest.mark.parametrize("claim, rule", BAD)
def test_bad_claims_caught(claim, rule):
    assert rule in {i.rule for i in check(claim).issues}


@pytest.mark.parametrize("title, code", [("software developer", 1020), ("janitor", 4220), ("registered nurse", 3255),
                                         ("cashier", 4720), ("customer service representative", 5240)])
def test_mapper_baseline(title, code):
    pytest.importorskip("ipumspy")
    from src.agents.mapper import map_title
    try:
        top = map_title(title, 1)[0]
    except FileNotFoundError:
        pytest.skip("DDI codebook not present")
    assert top.occ2010 == code
