"""Phase 11.5 pipeline with scripted stand-ins for the LLM (no Ollama needed)."""
import pytest

from src.agents.registry import REGISTRY_DIR
from src.agents.writer import TemplateError, WriterDraft, render

pytestmark = pytest.mark.skipif(not (REGISTRY_DIR / "phase8_main.json").exists(), reason="registry not built")

H = "{phase8_main.headline.pct}"
CI = "(95% CI {phase8_main.headline.lo} to {phase8_main.headline.hi})"
SCRIPT = [  # what a writer might do: invent a number, then drop the caveat, then get it right
    WriterDraft(template="Young workers in exposed jobs lost 19% of employment.", label="DESCRIPTIVE"),
    WriterDraft(template=f"Employment of 22-25-year-olds in Q5 occupations changed by {H} {CI}.", label="DESCRIPTIVE"),
    WriterDraft(template=f"Employment of 22-25-year-olds in Q5 occupations changed by {H} {CI} relative to Q1 "
                         "occupations and to ages 35-49.", label="DESCRIPTIVE"),
]


def scripted(drafts):
    it = iter(drafts)
    return lambda topic, keys, feedback: next(it)


def test_render_fills_numbers_from_registry_only():
    claim = render(SCRIPT[2])
    assert "14.1%" in claim.text and "{" not in claim.text and claim.refs[0] == "phase8_main.headline.pct"


@pytest.mark.parametrize("template, msg", [("lost 19% of jobs", "writes numbers"), ("{no.such.key} fell", "unknown")])
def test_render_rejects_literal_numbers_and_unknown_keys(template, msg):
    with pytest.raises(TemplateError, match=msg):
        render(WriterDraft(template=template, label="DESCRIPTIVE"))


def test_bad_claim_fixed_in_two_revisions():
    from src.agents.pipeline import run
    out = run("headline", {}, scripted(SCRIPT))
    assert out["status"] == "accepted" and out["attempts"] == 3
    assert out["history"][0]["issues"][0].startswith("structure")
    assert out["history"][1]["issues"][0].startswith("caveat")


def test_rejected_after_max_revisions():
    from src.agents.pipeline import run
    out = run("headline", {}, scripted([SCRIPT[0]] * 10), max_revisions=3)
    assert out["status"] == "rejected" and out["attempts"] == 4


def test_llm_mapper_cannot_leave_candidate_list():
    pytest.importorskip("ipumspy")
    from src.agents.mapper import map_title_llm
    try:
        assert map_title_llm("janitor", chooser=lambda t, c: 9999999).occ2010 == 4220   # invented code -> baseline
        second = map_title_llm("janitor", chooser=lambda t, c: c[1][0])                      # a valid pick is honoured
        assert second.occ2010 != 4220 and second.occ2010 in {c.occ2010 for c in __import__("src.agents.mapper", fromlist=["x"]).map_title("janitor", 10)}
    except FileNotFoundError:
        pytest.skip("DDI codebook not present")
