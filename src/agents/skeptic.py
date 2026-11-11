"""The Skeptic (Phase 11): rule-based checks on any claim before it is published.

Rules (Sections 11, 17; identification.md):
  label     every claim is labelled DESCRIPTIVE or CAUSAL_UNDER_ASSUMPTIONS
  number    every number in the text matches a registry value (|difference| <= 0.05, sign-free)
  causal    causal language only in a CAUSAL_UNDER_ASSUMPTIONS claim; "prove" never
  verdict   a Section 11 verdict phrase must be the headline's actual verdict
  units     a percent change (registry .pct/.lo/.hi) must not be called 'percentage points'
  caveat    quoting the headline % must (i) name the 35-49 comparison, (ii) give the within-22-25 Q5-vs-Q1
            estimate, and (iii) say that estimate is not significant (Aryan 2026-11-10). Together they are the
            finding: a large age gap, a weak exposure gradient among the young (Phase 8, L3)
  repeat    each registry key renders at most once per claim (catches garbled drafts)
  significance  "significant" / "not significant" in a clause must agree with the p-value (Holm-adjusted where
            Section 10 adjusts) of the estimate it describes: a cited value in the clause (at least one must
            agree), or, with no value in the clause, each quintile label it names (all must agree)
  quintile  a Q1-Q5 label in a clause must belong to a value cited there (Q1 is always the reference)
  number_required  a write-up claim with registry keys assigned must cite at least one (scoped; see writeup.py)
Rules significance, quintile, number_required: Aryan 2026-11-11.
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
TOL = 0.05 + 1e-9   # one-decimal rendering is at most 0.05 from the registry value; 1e-9 absorbs float error
CLAUSE = re.compile(r"(?<!\d)[.;](?!\d)|\b(?:but|while|whereas|in contrast)\b", re.I)
SIG_NEG = re.compile(r"not (?:statistically )?significant|insignificant|no (?:statistically )?significant", re.I)
SIG_POS = re.compile(r"(?:statistically )?significant", re.I)
QLABEL = re.compile(r"\bQ([1-5])\b")
TERM = re.compile(r"^(phase8_main\.terms\.q)(\d)(_a\d\d)\.")


def numbers_in(text: str) -> list[float]:
    for pat in NOT_NUMBERS:
        text = re.sub(pat, " ", text, flags=re.I)
    return [float(n) for n in NUMBER.findall(text)]


def base(key: str) -> str:
    return key.rsplit(".", 1)[0]


def p_value(reg: dict, b: str):
    return reg.get(b + ".holm_p", reg.get(b + ".p"))   # Holm where Section 10 adjusts


def quintiles(key: str) -> set[int] | None:
    m = TERM.match(key)
    if m:
        return {int(m.group(2)), 1}
    if any(s in key for s in ("headline.", "event_study_q5", "l3_within", "secondary_q5", "phase9_", "phase10_")):
        return {5, 1}
    return None   # not a quintile-specific estimate


def clauses(claim: Claim, reg: dict) -> list[tuple[str, list[str]]]:
    """Each clause with the cited registry keys whose values appear in it."""
    out = []
    for c in CLAUSE.split(claim.text):
        nums = numbers_in(c)
        keys = [k for k in dict.fromkeys(claim.refs)
                if isinstance(reg.get(k), (int, float)) and any(abs(n - abs(reg[k])) <= TOL for n in nums)]
        out.append((c, keys))
    return out


def significance_checks(claim: Claim) -> list[tuple[str, str, bool]]:
    """(clause, phrase, consistent) for every clause whose significance statement could be checked."""
    reg, out = registry.load(), []
    for c, keys in clauses(claim, reg):
        neg, pos = SIG_NEG.search(c), SIG_POS.search(SIG_NEG.sub(" ", c))
        if bool(neg) == bool(pos):   # no statement, or both in one clause: not checkable
            continue
        says_sig = bool(pos)
        bases = {base(k) for k in keys if p_value(reg, base(k)) is not None}
        if bases:      # a cited value in the clause: at least one estimate must agree
            ok = any((p_value(reg, b) < 0.05) == says_sig for b in bases)
        else:          # labels only, e.g. "no significant difference in Q2 and Q3": every named quintile must agree
            fam = next((TERM.match(k) for k in claim.refs if TERM.match(k)), None)
            if not fam:
                continue
            bs = [f"{fam.group(1)}{q}{fam.group(3)}" for q in {int(x) for x in QLABEL.findall(c)} - {1}]
            bs = [b for b in bs if p_value(reg, b) is not None]
            if not bs:
                continue
            ok = all((p_value(reg, b) < 0.05) == says_sig for b in bs)
        out.append((c, (neg or pos).group(0), ok))
    return out


def check(claim: Claim, require_number: bool = False) -> SkepticReport:
    rep, reg = SkepticReport(claim), registry.load()
    known = [abs(v) for v in registry.numbers()]
    text = claim.text

    if claim.label not in LABELS:
        rep.issues.append(Issue("label", f"label {claim.label!r} is not one of {sorted(LABELS)}", claim.label))
    for n in numbers_in(text):
        if n not in DESIGN_CONSTANTS and not any(abs(n - k) <= TOL for k in known):
            rep.issues.append(Issue("number", f"{n:g} is not a reported number", f"{n:g}"))
    if CAUSAL.search(text) and claim.label != "CAUSAL_UNDER_ASSUMPTIONS":
        rep.issues.append(Issue("causal", f"causal wording in a {claim.label} claim", CAUSAL.search(text).group(0)))
    if PROVE.search(text):
        rep.issues.append(Issue("causal", "'prove' overstates any estimate", PROVE.search(text).group(0)))

    actual = reg["phase8_main.headline.verdict"].split(":")[0].lower()
    for v in VERDICTS:
        if v in text.lower() and v != actual and re.search(r"headline|Q5", text, re.I):
            rep.issues.append(Issue("verdict", f"the headline verdict is {actual!r}", v))
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
            rep.issues.append(Issue("units", "a percent change in employment is called 'percentage points'",
                                    re.search(r"percentage[- ]points?|\bpp\b", text, re.I).group(0)))
    nums = numbers_in(text)
    near = lambda x: any(abs(n - abs(x)) <= TOL for n in nums)
    if near(reg["phase8_main.headline.pct"]):
        missing = []
        if not re.search(r"35-49|older", text, re.I):
            missing.append("the 35-49 comparison")
        if not near(reg["phase8_main.l3_within_age_q5_vs_q1.22-25.pct"]):
            missing.append("the within-22-25 Q5-vs-Q1 estimate")
        if not re.search(r"not (?:statistically )?significant|insignificant|no (?:statistically )?significant", text, re.I):
            missing.append("that the within-22-25 estimate is not significant")
        if missing:
            rep.issues.append(Issue("caveat", "quotes the headline without " + ", ".join(missing),
                                    f"{abs(reg['phase8_main.headline.pct']):.1f}"))
    dup = sorted({k for k in claim.refs if claim.refs.count(k) > 1})
    if dup:
        rep.issues.append(Issue("repeat", "renders the same registry value more than once", ", ".join(dup)))
    for c, phrase, ok in significance_checks(claim):
        if not ok:
            rep.issues.append(Issue("significance", "the significance statement disagrees with the estimate's p-value", phrase))
    for c, keys in clauses(claim, reg):
        allowed = set().union(*[quintiles(k) for k in keys if quintiles(k) is not None])
        bad = sorted({int(q) for q in QLABEL.findall(c)} - allowed) if allowed else []
        for q in bad:
            rep.issues.append(Issue("quintile", "the quintile label does not match the value cited beside it", f"Q{q}"))
    if require_number and not claim.refs:
        rep.issues.append(Issue("number_required", "a write-up claim with registry keys assigned must cite at least one"))
    return rep
