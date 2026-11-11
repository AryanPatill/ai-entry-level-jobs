"""The Writer (Phase 11): the LLM drafts a sentence template; code fills in the numbers.

Structural guarantee (not a prompt instruction): the LLM's output is a template with {registry.key}
placeholders. `render` rejects any template that writes a number itself (apart from the two design
constants) or names a key that is not in the registry, and only then substitutes registry values.
So every number in a rendered claim comes from the registry.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from src.agents import registry
from src.agents.schemas import Claim
from src.agents.skeptic import DESIGN_CONSTANTS, numbers_in

PLACEHOLDER = re.compile(r"\{([^{}]+)\}")


class WriterDraft(BaseModel):
    template: str = Field(description="One sentence. Every number must be a {registry.key} placeholder; write no digits.")
    label: Literal["DESCRIPTIVE", "CAUSAL_UNDER_ASSUMPTIONS"]


class TemplateError(ValueError):
    pass


def fmt(key: str, v) -> str:
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return str(v)
    if key.endswith((".pct", ".lo", ".hi")) or key.endswith("_pct"):
        return f"{v:+.1f}%"
    if key.endswith((".p", "_p")) or key.split(".")[-1].startswith("p_"):
        return f"{v:.3f}"
    return f"{v:g}"


def render(draft: WriterDraft) -> Claim:
    reg = registry.load()
    keys = PLACEHOLDER.findall(draft.template)
    unknown = [k for k in keys if k not in reg]
    if unknown:
        raise TemplateError(f"unknown registry keys: {unknown}")
    literal = [n for n in numbers_in(PLACEHOLDER.sub(" ", draft.template)) if n not in DESIGN_CONSTANTS]
    if literal:
        raise TemplateError(f"the template writes numbers itself: {literal}; use registry placeholders",
                            *[f"{n:g}" for n in literal])
    # A "%" or " percent" typed right after a placeholder is absorbed when the value already carries "%"
    # (no "-14.1%%" or "-14.1% percent").
    text = re.sub(r"\{([^{}]+)\}(%| percent\b)?", lambda m: (lambda v: v if v.endswith("%") else v + (m.group(2) or ""))(
        fmt(m.group(1), reg[m.group(1)])), draft.template)
    return Claim(text, draft.label, tuple(keys))


def keys_for(*prefixes: str) -> dict:
    """The registry entries a Writer may cite for a topic: numbers and short labels, not whole sentences."""
    return {k: v for k, v in registry.load().items()
            if k.startswith(prefixes) and (not isinstance(v, str) or len(v) <= 40)}


HEADLINE_RULE = ("- The headline (Q5 x ages 22-25) is relative to Q1 and to ages 35-49. Say so, and also give the "
                 "within-ages-22-25 Q5-vs-Q1 change and say it is not statistically significant.\n")
PROMPT = """You write one sentence for a research write-up on whether AI is reducing employment of young
workers (ages 22-25) in AI-exposed occupations. Rules:
- Never write a digit. Every number must be a placeholder copied exactly from the key list, e.g. {{phase8_main.headline.pct}}.
- Label the sentence DESCRIPTIVE unless it states an effect under the study's assumptions (CAUSAL_UNDER_ASSUMPTIONS).
- No causal verbs (caused, led to, due to AI) in a DESCRIPTIVE sentence. Never say "prove".
- Every estimate is relative to ages 35-49 and to the least exposed quintile (Q1). Name the quintile of each value
  as its key says (q2 = Q2, ...); do not call a value "the headline" unless its key is phase8_main.headline.
{headline}- Use each placeholder at most once.
Topic: {topic}
Keys you may use (key = current value, for context only; do not copy the value):
{keys}
{feedback}"""


# Skeptic rule -> the concrete requirement the Writer must meet on its next draft.
REQUIREMENTS = {
    "caveat": ("REQUIRED: say 'relative to ages 35-49' AND give the within-ages-22-25 Q5-vs-Q1 change "
               "{phase8_main.l3_within_age_q5_vs_q1.22-25.pct} AND state that it is not statistically significant."),
    "repeat": "REQUIRED: use each {placeholder} at most once.",
    "units": "REQUIRED: say 'percent', never 'percentage point', for these changes in employment.",
    "structure": "REQUIRED: write no digits at all; every number must be a {placeholder} from the key list.",
    "causal": "REQUIRED: no causal verbs (caused, led to, due to, because of AI) and never 'prove'.",
}


def feedback_text(feedback: list[str]) -> str:
    if not feedback:
        return ""
    rules = {f.split(":")[0] for f in feedback}
    musts = [REQUIREMENTS[r] for r in sorted(rules) if r in REQUIREMENTS]
    return ("Your previous draft was rejected for: " + "; ".join(feedback) + ".\n" + "\n".join(musts)
            + "\nWrite a new sentence that meets every requirement.")


def llm_writer(model: str | None = None):
    from src.agents.llm import cfg, chat
    first = chat(model).with_structured_output(WriterDraft)
    retry = chat(model, cfg()["retry_temperature"]).with_structured_output(WriterDraft)

    def write(topic: str, keys: dict, feedback: list[str]) -> WriterDraft:
        listing = "\n".join(f"{k} = {v}" for k, v in keys.items())
        # Headline instructions only when the headline is citable; elsewhere they pulled drafts toward "Q5".
        headline = HEADLINE_RULE if "phase8_main.headline.pct" in keys else ""
        return (retry if feedback else first).invoke(PROMPT.format(topic=topic, keys=listing, headline=headline,
                                                                   feedback=feedback_text(feedback)))
    return write
