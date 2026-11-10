"""Phase 11.5: the LangGraph claim pipeline.

    write (LLM: template + label) -> render (code: validate template, fill registry numbers)
      -> skeptic (code rules; then optional LLM review, which may only add issues)
      -> accepted | revise (issues fed back to write) | rejected after max_revisions

The writer and reviewer are injected callables, so the graph is tested with scripted stand-ins and run
with the local model in use. No node lets an LLM put a number into a claim (see writer.render).
"""
from __future__ import annotations

from typing import Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from src.agents.schemas import Claim, Issue
from src.agents.skeptic import check
from src.agents.writer import TemplateError, WriterDraft, render


class State(TypedDict, total=False):
    topic: str
    keys: dict
    draft: WriterDraft
    claim: Optional[Claim]
    issues: list[Issue]
    attempts: int
    history: list[dict]
    status: str


class Review(BaseModel):
    issues: list[str]


def build_graph(writer: Callable, reviewer: Callable | None = None, max_revisions: int = 3):
    def write(s: State) -> State:
        feedback = [f"{i.rule}: {i.detail}" for i in s.get("issues", [])]
        return {"draft": writer(s["topic"], s["keys"], feedback), "attempts": s.get("attempts", 0) + 1}

    def render_node(s: State) -> State:
        try:
            return {"claim": render(s["draft"]), "issues": []}
        except TemplateError as e:
            return {"claim": None, "issues": [Issue("structure", str(e))]}

    def skeptic(s: State) -> State:
        issues = list(s["issues"])
        if s["claim"] is not None:
            issues += check(s["claim"]).issues
            if not issues and reviewer is not None:
                issues += [Issue("review", t) for t in reviewer(s["claim"])]
        hist = s.get("history", []) + [{"attempt": s["attempts"], "template": s["draft"].template,
                                       "claim": s["claim"].text if s["claim"] else None,
                                       "issues": [f"{i.rule}: {i.detail}" for i in issues]}]
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

    def review(claim: Claim) -> list[str]:
        out = structured.invoke(
            "Review this sentence from an economics write-up for overstatement: causal claims beyond its label "
            f"({claim.label}), missing uncertainty, or wording that hides that the comparison is relative to older "
            "workers and less-exposed occupations. Return an empty list if it is fine. Do not suggest numbers.\n"
            f"Sentence: {claim.text}")
        return out.issues
    return review


def run(topic: str, keys: dict, writer: Callable, reviewer: Callable | None = None, max_revisions: int = 3) -> State:
    return build_graph(writer, reviewer, max_revisions).invoke({"topic": topic, "keys": keys})
