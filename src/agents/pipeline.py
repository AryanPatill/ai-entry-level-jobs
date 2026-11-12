"""Phase 11.5: the LangGraph claim pipeline.

    write (LLM: template + label) -> render (code: validate template, fill registry numbers)
      -> skeptic (code rules; then optional LLM review, which may only add issues)
      -> accepted | revise (issues fed back to write) | rejected after max_revisions

The writer and reviewer are injected callables, so the graph is tested with scripted stand-ins and run
with the local model in use. No node lets an LLM put a number into a claim (see writer.render).
"""
from __future__ import annotations

import re
from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from src.agents import registry
from src.agents.schemas import Claim, Issue
from src.agents.skeptic import SIG_POS, check, significance_checks
from src.agents.writer import TemplateError, WriterDraft, fmt, render

# The design's required comparison wording (Section 8 reference groups); not the Writer's to defend.
COMPARISON = re.compile(r"\b(?:relative to|compared (?:to|with)|versus|vs\.?)\s+(?:the\s+)?"
                        r"(?:ages\s+35-49|35-49|Q1|least[- ]exposed\w*(?:\s+\w+)?)(?:\s+(?:and|or)\s+(?:to\s+)?"
                        r"(?:the\s+)?(?:ages\s+35-49|35-49|Q1|least[- ]exposed\w*(?:\s+\w+)?))?", re.I)


class State(TypedDict, total=False):
    topic: str
    keys: dict
    draft: WriterDraft
    claim: Optional[Claim]
    issues: list[Issue]
    attempts: int
    history: list[dict]
    status: str


class Finding(BaseModel):
    quote: str      # the exact words in the sentence that cause the problem
    problem: str


class Review(BaseModel):
    findings: list[Finding]


def grounded(claim: Claim, findings: list[Finding]) -> list[Issue]:
    """Keep a reviewer objection only if it quotes the Writer's own words (Aryan 2026-11-10, option 1b).

    Dropped: quotes not in the sentence or under 8 characters (small models echo their checklist), and
    quotes that overlap a value the code filled in from the registry (numbers, the preregistered verdict
    label): those are the analysis's words, not the Writer's, and the reviewer cannot overrule them.
    """
    reg = registry.load()
    text = claim.text.lower()
    filled = [fmt(k, reg[k]).lower() for k in claim.refs if k in reg]
    verified = [c.lower() for c, _, ok in significance_checks(claim) if ok]   # rule 4 (Aryan 2026-11-11)
    keep = []
    for f in findings:
        q = f.quote.strip().lower()
        if len(q) < 8 or q not in text or any(v in q or q in v for v in filled):
            continue
        if SIG_POS.search(q) and any(q in c or c.strip() in q for c in verified):
            continue   # significance already checked against the p-value
        if COMPARISON.search(q) and len(re.sub(r"\W+", "", COMPARISON.sub("", q))) < 8:
            continue   # the objection is to the required comparison wording itself (rule 4, extended 2026-11-11)
        keep.append(Issue("review", f.problem, f.quote.strip()))
    return keep


def build_graph(writer: Callable, reviewer: Callable | None = None, max_revisions: int = 3, require_number: bool = False):
    def write(s: State) -> State:
        feedback = [f"{i.rule}: {i.detail}" + (f" (\"{i.quote}\")" if i.quote else "") for i in s.get("issues", [])]
        return {"draft": writer(s["topic"], s["keys"], feedback), "attempts": s.get("attempts", 0) + 1}

    def render_node(s: State) -> State:
        try:
            return {"claim": render(s["draft"]), "issues": []}
        except TemplateError as e:
            return {"claim": None, "issues": [Issue("structure", str(e), ", ".join(str(n) for n in e.args[1:]) if len(e.args) > 1 else "")]}

    def skeptic(s: State) -> State:
        issues = list(s["issues"])
        if s["claim"] is not None:
            issues += check(s["claim"], require_number).issues
            if not issues and reviewer is not None:
                issues += reviewer(s["claim"])
        hist = s.get("history", []) + [{"attempt": s["attempts"], "template": s["draft"].template,
                                       "claim": s["claim"].text if s["claim"] else None,
                                       "issues": [{"rule": i.rule, "detail": i.detail, "quote": i.quote} for i in issues]}]
        status = "accepted" if not issues else ("rejected" if s["attempts"] > max_revisions else "revise")
        return {"issues": issues, "history": hist, "status": status}

    g = StateGraph(State)
    g.add_node("write", write)
    g.add_node("render", render_node)
    g.add_node("skeptic", skeptic)
    g.set_entry_point("write")
    g.add_edge("write", "render")
    g.add_edge("render", "skeptic")
    g.add_conditional_edges("skeptic", lambda s: s["status"], {"revise": "write", "accepted": END, "rejected": END})
    return g.compile()


def llm_reviewer(model: str | None = None):
    from src.agents.llm import chat
    structured = chat(model).with_structured_output(Review)

    def review(claim: Claim) -> list[Issue]:
        out = structured.invoke(
            "Review this sentence from an economics write-up. Report a finding only for a real problem: a causal claim "
            f"stronger than its label ({claim.label}), or wording that overstates certainty. For each finding, copy the "
            "exact words from the sentence that cause it into `quote`. If no words in the sentence cause a problem, "
            "return an empty list. Do not suggest numbers.\n"
            f"Sentence: {claim.text}")
        return grounded(claim, out.findings)
    return review


def run(topic: str, keys: dict, writer: Callable, reviewer: Callable | None = None, max_revisions: int = 3,
        require_number: bool = False) -> State:
    return build_graph(writer, reviewer, max_revisions, require_number).invoke({"topic": topic, "keys": keys})
