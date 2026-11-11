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
        raise TemplateError(f"the template writes numbers itself: {literal}; use registry placeholders")
    # A "%" typed right after a placeholder is absorbed when the value already carries one (no "-14.1%%").
    text = re.sub(r"\{([^{}]+)\}(%?)", lambda m: (lambda v: v if v.endswith("%") else v + m.group(2))(
        fmt(m.group(1), reg[m.group(1)])), draft.template)
    return Claim(text, draft.label, tuple(keys))


def keys_for(*prefixes: str) -> dict:
    """The registry entries a Writer may cite for a topic: numbers and short labels, not whole sentences."""
    return {k: v for k, v in registry.load().items()
            if k.startswith(prefixes) and (not isinstance(v, str) or len(v) <= 40)}


PROMPT = """You write one sentence for a research write-up on whether AI is reducing employment of young
workers (ages 22-25) in AI-exposed occupations. Rules:
- Never write a digit. Every number must be a placeholder copied exactly from the key list, e.g. {{phase8_main.headline.pct}}.
- Label the sentence DESCRIPTIVE unless it states an effect under the study's assumptions (CAUSAL_UNDER_ASSUMPTIONS).
- No causal verbs (caused, led to, due to AI) in a DESCRIPTIVE sentence. Never say "prove".
- The headline is relative: young vs ages 35-49, and exposed (Q5) vs least exposed (Q1) occupations. Say so.
Topic: {topic}
Keys you may use (key = current value, for context only; do not copy the value):
{keys}
{feedback}"""


def llm_writer(model: str | None = None):
    from src.agents.llm import chat
    structured = chat(model).with_structured_output(WriterDraft)

    def write(topic: str, keys: dict, feedback: list[str]) -> WriterDraft:
        fb = ("Your previous draft was rejected for: " + "; ".join(feedback) + ". Fix every point.") if feedback else ""
        listing = "\n".join(f"{k} = {v}" for k, v in keys.items())
        return structured.invoke(PROMPT.format(topic=topic, keys=listing, feedback=fb))
    return write
