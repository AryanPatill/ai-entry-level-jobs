"""The Skeptic (Phase 11): rule-based checks on any claim before it is published.

Rules (Sections 11, 17; identification.md):
  label     every claim is labelled DESCRIPTIVE or CAUSAL_UNDER_ASSUMPTIONS
  number    every number in the text matches a registry value (|difference| <= 0.05, sign-free)
  causal    causal language only in a CAUSAL_UNDER_ASSUMPTIONS claim; "prove" never
  verdict   a Section 11 verdict phrase must be the headline's actual verdict
  units     a percent change (registry .pct/.lo/.hi) must not be called 'percentage points'
  caveat    quoting the headline % must name the comparison (35-49 / older workers), because most of the
            estimate comes from the comparison group (Phase 8, L3)
An LLM Skeptic can be layered on top later; these rules run first and cannot be argued with.
"""
from __future__ import annotations

import re

from src.agents import registry
from src.agents.schemas import Claim, Issue, SkepticReport

LABELS = {"DESCRIPTIVE", "CAUSAL_UNDER_ASSUMPTIONS"}
# Identifiers that contain digits but are not quantities; stripped before numbers are checked.
NOT_NUMBERS = [r"\b\d{2}-\d{2}\b",               # age groups 22-25, 35-49
               r"\bQ[1-5]\b",                    # quintiles
               r"\b(?:19|20)\d{2}(?:-\d{2})?\b",  # years and year-months
               r"\bSection \d+\b", r"\bphase \d+\b", r"\bT[1-7]\b", r"\bL[1-4]\b"]
# Design constants: numbers fixed by the preregistration, not results. Closed list: a new entry needs a
# recorded reason (decisions.md) and a test in tests/test_agents.py; never add one to silence a false positive.
DESIGN_CONSTANTS = {
    95.0: "confidence level of every reported interval (Sections 10-11)",
    5.0: "preregistered equivalence band, ±5% (Section 11)",
}
NUMBER = re.compile(r"\d+(?:\.\d+)?")
CAUSAL = re.compile(r"\b(caus(?:e|ed|es|ing)|because of AI|due to AI|AI (?:is |has )?(?:killing|destroying|taking|stealing|eliminat\w+)|led to)\b", re.I)
PROVE = re.compile(r"\bprov(?:e|es|ed|ing)\b", re.I)
VERDICTS = ("effect detected", "no meaningful effect", "inconclusive")
TOL = 0.05


def numbers_in(text: str) -> list[float]:
    for pat in NOT_NUMBERS:
        text = re.sub(pat, " ", text, flags=re.I)
    return [float(n) for n in NUMBER.findall(text)]


def check(claim: Claim) -> SkepticReport:
    rep, reg = SkepticReport(claim), registry.load()
    known = [abs(v) for v in registry.numbers()]
    text = claim.text

    if claim.label not in LABELS:
        rep.issues.append(Issue("label", f"label {claim.label!r} is not one of {sorted(LABELS)}"))
    for n in numbers_in(text):
        if n not in DESIGN_CONSTANTS and not any(abs(n - k) <= TOL for k in known):
            rep.issues.append(Issue("number", f"{n:g} is not a reported number"))
    if CAUSAL.search(text) and claim.label != "CAUSAL_UNDER_ASSUMPTIONS":
        rep.issues.append(Issue("causal", f"causal wording {CAUSAL.search(text).group(0)!r} in a {claim.label} claim"))
    if PROVE.search(text):
        rep.issues.append(Issue("causal", "'prove' overstates any estimate"))

    actual = reg["phase8_main.headline.verdict"].split(":")[0].lower()
    for v in VERDICTS:
        if v in text.lower() and v != actual and re.search(r"headline|Q5", text, re.I):
            rep.issues.append(Issue("verdict", f"says {v!r}; the headline verdict is {actual!r}"))
    if re.search(r"percentage[- ]points?|\bpp\b", text, re.I):
        is_pct = lambda k: k.endswith((".pct", ".lo", ".hi")) and ".secondary_" not in k
        if claim.refs:   # a Writer claim names its registry keys exactly
            wrong = any(is_pct(k) for k in claim.refs)
        else:            # free text: a number counts as a % change only if it matches no result reported in points
            vals = lambda pred: [abs(v) for k, v in reg.items() if pred(k) and isinstance(v, (int, float))]
            changes = vals(is_pct)
            points = vals(lambda k: ".secondary_" in k and k.endswith((".coef", ".lo", ".hi")))
            near = lambda n, xs: any(abs(n - x) <= TOL for x in xs)
            wrong = any(near(n, changes) and not near(n, points) for n in numbers_in(text))
        if wrong:
            rep.issues.append(Issue("units", "a percent change in employment is called 'percentage points'"))
    head = abs(reg["phase8_main.headline.pct"])
    if any(abs(n - head) <= TOL for n in numbers_in(text)) and not re.search(r"35-49|older|comparison", text, re.I):
        rep.issues.append(Issue("caveat", "quotes the headline without naming the 35-49 comparison it is relative to"))
    return rep
