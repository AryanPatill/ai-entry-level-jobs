"""The Mapper (Phase 11), baseline version: free-text job title -> OCC2010 candidates.

Deterministic baseline, no LLM: score = 0.5 x difflib similarity to the IPUMS OCC2010 label
+ 0.5 x share of title words that start a label word (first 5 letters, so "janitor" hits "Janitors").
Phase 12 measures its accuracy; an LLM Mapper must beat it to be used.
"""
from __future__ import annotations

import difflib
import re
from functools import lru_cache

from ipumspy import readers

from src.agents.schemas import MapperResult
from src.data.convert_to_parquet import locate_files
from src.data.inspect_codes import labels_for
from src.data.ipums_extract import load_log

WORD = re.compile(r"[a-z]+")


@lru_cache(maxsize=1)
def labels() -> dict[int, str]:
    out = labels_for(readers.read_ipums_ddi(locate_files(load_log())[2]), "OCC2010")
    return {k: v for k, v in out.items() if k != 9999}


def score(title: str, label: str) -> float:
    t, l = title.lower(), label.lower()
    tw, lw = WORD.findall(t), WORD.findall(l)
    hits = sum(any(w.startswith(x[:5]) for w in lw) for x in tw) / max(len(tw), 1)
    return 0.5 * difflib.SequenceMatcher(None, t, l).ratio() + 0.5 * hits


def map_title(title: str, k: int = 3) -> list[MapperResult]:
    ranked = sorted(labels().items(), key=lambda kv: score(title, kv[1]), reverse=True)[:k]
    return [MapperResult(title, code, lab, round(score(title, lab), 3)) for code, lab in ranked]


def map_title_llm(title: str, chooser=None, k: int = 10) -> MapperResult:
    """LLM Mapper: the model picks one of the baseline's top-k candidates; anything else falls back to baseline top-1.

    `chooser(title, candidates) -> int` is injected (an LLM in use, a stand-in in tests). It can only choose
    among existing codes, never invent one.
    """
    cands = map_title(title, k)
    if chooser is None:
        return cands[0]
    try:
        pick = int(chooser(title, [(c.occ2010, c.label) for c in cands]))
    except Exception:   # model unavailable or unparseable answer
        return cands[0]
    return next((c for c in cands if c.occ2010 == pick), cands[0])


def llm_chooser(model: str | None = None):
    from pydantic import BaseModel

    from src.agents.llm import chat

    class Pick(BaseModel):
        occ2010: int

    structured = chat(model).with_structured_output(Pick)

    def choose(title: str, candidates: list[tuple[int, str]]) -> int:
        listing = "\n".join(f"{code}: {lab}" for code, lab in candidates)
        return structured.invoke(f"Which Census occupation best matches the job title '{title}'? "
                                 f"Answer with one code from this list only.\n{listing}").occ2010
    return choose
