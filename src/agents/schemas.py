"""Typed handoffs between agents (Phase 11). Stdlib dataclasses; no agent ever produces a number.

Writer -> Claim -> Skeptic -> SkepticReport.   Title -> Mapper -> MapperResult.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Claim:
    text: str
    label: str                      # DESCRIPTIVE or CAUSAL_UNDER_ASSUMPTIONS (Section 17); the Skeptic checks it
    refs: tuple[str, ...] = ()      # registry keys the claim relies on


@dataclass(frozen=True)
class Issue:
    rule: str
    detail: str
    quote: str = ""     # the exact text that triggered the rule (empty when the problem is an absence)


@dataclass
class SkepticReport:
    claim: Claim
    issues: list[Issue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class MapperResult:
    title: str
    occ2010: int
    label: str
    score: float
