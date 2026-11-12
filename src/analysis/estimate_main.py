"""Phase 8: Section 8 main model, Section 9 event study, Section 6 secondary outcomes, Section 11 verdicts.

Main model (Section 8), main sample (2015-01 on, pandemic months excluded), ages 22-25, 26-34, 35-49:
    E[Y] = exp( sum_{q=2..5, a in 22-25, 26-34} beta_qa 1[Q=q] 1[a] Post + occ x age + occ x month + age x month )
Poisson PML (pyfixest fepois), CRV1 by occupation; weights enter through the outcome (weighted counts).
Verdict (Section 11): 95% CI against ln(0.95), ln(1.05); TOST at alpha = 0.025 per side; required wording.
Event study (Section 9): Post replaced by quarterly bins from 2022-12, reference bin -1 (Sep-Nov 2022).
Pre-trend rule: joint Wald test of the pre-period Q5 x 22-25 bins, p < 0.05, or any pre bin CI beyond +/-5%.
Secondary (Section 6): unemployment rate and mean hours, weighted linear, same fixed effects; Holm (Section 10).
L3 (exploratory, identification.md): Q5-vs-Q1 change within 22-25 alone and within 35-49 alone.

Run from the repo root:  python -m src.analysis.estimate_main
"""
from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyfixest as pf
from scipy import stats

from src.analysis.eda_stage_b import BASE_BIN, FIGDIR, GRID, INK, INK2, SERIES, SURFACE, add_bin, bin_start, style
from src.utils.config import REPO_ROOT, load_settings

TABLE = REPO_ROOT / "results" / "tables" / "phase8_main.md"
REGISTRY = REPO_ROOT / "results" / "registry"
LO, HI = math.log(0.95), math.log(1.05)
AGES = ["22-25", "26-34", "35-49"]
YOUNG = ("22-25", "26-34")
FE = "occ2010^age_group + occ2010^ym + age_group^ym"
VCOV = {"CRV1": "occ2010"}


def pct(x: float) -> str:
    return f"{100 * (math.exp(x) - 1):+.1f}%"


def verdict(b: float, lo: float, hi: float, group: str) -> str:
    """Section 11 wording, fixed 2026-10-04."""
    ci = f"{pct(b)} (95% CI {pct(lo)} to {pct(hi)})"
    if hi < LO or lo > HI:
        return (f"Effect detected: employment of {group} changed by {ci}, beyond the preregistered "
                "±5% threshold.")
    if lo >= LO and hi <= HI:
        return f"No meaningful effect: the change is {ci}, inside the preregistered ±5% band; equivalence established."
    text = f"Inconclusive: the change is {ci}. The data cannot distinguish an effect beyond ±5% from one inside it."
    if hi < 0 or lo > 0:
        text += " The estimate differs from zero but does not meet the preregistered threshold."
    return text


def tost(b: float, se: float) -> tuple[float, float]:
    """One-sided p-values against the lower and upper equivalence bounds (normal approximation)."""
    return 1 - stats.norm.cdf((b - LO) / se), stats.norm.cdf((b - HI) / se)


def est(r: pd.Series) -> dict:
    """A coefficient as the reports state it: % change, 95% CI in %, p."""
    f = lambda v: round(100 * (math.exp(v) - 1), 2)
    return {"pct": f(r.b), "lo": f(r.lo), "hi": f(r.hi), "p": round(float(r.p), 4)}


def record(name: str, data: dict) -> None:
    """Numbers the agent layer may cite (Phase 11). The only source of numbers for agents."""
    REGISTRY.mkdir(parents=True, exist_ok=True)
    (REGISTRY / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def holm(p: dict[str, float]) -> dict[str, float]:
    order = sorted(p, key=p.get)
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * p[k]))
        out[k] = run
    return out


def main_terms(p: pd.DataFrame, post: pd.Series, ages=YOUNG, prefix: str = "q") -> list[str]:
    """Adds quintile x age x `post` indicators (Q2-Q5) to `p` in place; returns their names."""
    terms = []
    for q in (2, 3, 4, 5):
        for a in ages:
            name = f"{prefix}{q}_a{a[:2]}"
            p[name] = ((p.quintile == q) & (p.age_group == a)).astype(int) * post.astype(int)
            terms.append(name)
    return terms


def coef_table(fit, terms) -> pd.DataFrame:
    ci = fit.confint()
    return pd.DataFrame({"b": fit.coef()[terms], "se": fit.se()[terms], "lo": ci.loc[terms].iloc[:, 0],
                         "hi": ci.loc[terms].iloc[:, 1], "p": fit.pvalue()[terms]})


def event_study(p: pd.DataFrame, base: int = BASE_BIN):
    p = add_bin(p)
    bins = sorted(b for b in p.bin.unique() if b != base)
    names = []
    for b in bins:
        for q in (2, 3, 4, 5):
            for a in YOUNG:
                n = f"e{q}_{a[:2]}_{'m' if b < 0 else 'p'}{abs(b)}"
                p[n] = ((p.quintile == q) & (p.age_group == a) & (p.bin == b)).astype(int)
                names.append((n, b, q, a))
    fit = pf.fepois(f"emp_w ~ {' + '.join(n for n, *_ in names)} | {FE}", data=p, vcov=VCOV)
    es = pd.DataFrame(names, columns=["term", "bin", "q", "age"]).set_index("term")
    es = es.join(coef_table(fit, list(es.index)))
    head = es[(es.q == 5) & (es.age == "22-25")]
    pre = head[head.bin < 0]
    idx = [list(fit.coef().index).index(t) for t in pre.index]
    V = fit._vcov[np.ix_(idx, idx)]
    wald = float(pre.b.values @ np.linalg.solve(V, pre.b.values))
    p_joint = 1 - stats.chi2.cdf(wald, len(pre))
    beyond = pre[(pre.hi < LO) | (pre.lo > HI)]
    return head, p_joint, len(pre), beyond


def es_figure(head: pd.DataFrame) -> None:
    full = pd.concat([head[["bin", "b", "lo", "hi"]], pd.DataFrame({"bin": [BASE_BIN], "b": [0.0], "lo": [0.0], "hi": [0.0]})]).sort_values("bin")
    full = full.set_index("bin").reindex(range(int(full.bin.min()), int(full.bin.max()) + 1))
    xs = [bin_start(b) for b in full.index]
    f = lambda v: 100 * (np.exp(v) - 1)
    fig, ax = plt.subplots(figsize=(9, 4.4), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.axhspan(f(LO), f(HI), color=GRID, alpha=0.6, lw=0)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(bin_start(0), color=INK2, lw=0.8, ls=":")
    ax.fill_between(xs, f(full.lo), f(full.hi), color=SERIES[0], alpha=0.18, lw=0)
    ax.plot(xs, f(full.b), color=SERIES[0], lw=2)
    ax.plot(bin_start(BASE_BIN), 0, "o", ms=8, color=SERIES[0], mec=SURFACE, mew=2)
    ax.set_title("Event study: Q5 x ages 22-25, relative to Q1 and ages 35-49 (Section 9)", loc="left", color=INK, fontsize=11)
    ax.set_ylabel("Percent change vs Sep-Nov 2022 (95% CI)", color=INK2)
    ax.text(0, -0.13, "Poisson PML; occupation x age, occupation x month, age x month FE; CRV1 by occupation. "
            "Grey band: ±5%. Dot: reference bin.", transform=ax.transAxes, color=INK2, fontsize=8)
    style(ax)
    fig.tight_layout()
    fig.savefig(FIGDIR / "phase8_event_study.png", dpi=150)


def main() -> None:
    s = load_settings()
    d = s["design"]
    p = pd.read_parquet(s["paths"]["processed"] / "panel_occ_age_month.parquet")
    p = p[p.main_sample & p.age_group.isin(AGES)].copy()

    # 8.1 Main model.
    terms = main_terms(p, p.post)
    fit = pf.fepois(f"emp_w ~ {' + '.join(terms)} | {FE}", data=p, vcov=VCOV)
    ct = coef_table(fit, terms)
    h = ct.loc["q5_a22"]
    t_lo, t_hi = tost(h.b, h.se)

    # 8.2 Event study.
    head, p_joint, k_pre, beyond = event_study(p.copy())
    es_figure(head)
    flagged = p_joint < 0.05 or len(beyond) > 0

    # 8.3 Secondary outcomes, weighted linear, same fixed effects.
    sec = {}
    for name, y, w in (("Unemployment rate (points)", "urate", "lf"), ("Mean usual weekly hours", "hours", "emp_w")):
        q = p.assign(lf=p.emp_w + p.unemp_w)
        q = q[q.lf > 0].copy()
        q["urate"] = 100 * q.unemp_w / q.lf
        q["hours"] = q.hours_wsum / q.hours_w.where(q.hours_w > 0)   # NaN without hours; dropna removes those rows
        q = q.dropna(subset=[y])
        f2 = pf.feols(f"{y} ~ {' + '.join(terms)} | {FE}", data=q, weights=w, vcov=VCOV)
        sec[name] = coef_table(f2, terms).loc["q5_a22"]
    holm_p = holm({k: r.p for k, r in sec.items()})

    # 8.4 L3 (exploratory): within-age DiD, Q2-Q5 x post, occupation and month fixed effects.
    l3 = {}
    for a in ("22-25", "35-49"):
        q = p[p.age_group == a].copy()
        dterms = []
        for k in (2, 3, 4, 5):
            q[f"d{k}"] = (q.quintile == k).astype(int) * q.post.astype(int)
            dterms.append(f"d{k}")
        l3[a] = coef_table(pf.fepois(f"emp_w ~ {' + '.join(dterms)} | occ2010 + ym", data=q, vcov=VCOV), dterms).loc["d5"]

    # Report.
    n_obs, n_cl = fit._N, fit._G[0]
    lines = ["# Phase 8: main model, event study, secondary outcomes", "",
             "Generated by `python -m src.analysis.estimate_main`. Preregistration v1.0, Sections 8-11. Main sample",
             f"({d['main_start']} on, {d['excluded_start']} to {d['excluded_end']} excluded), ages 22-25, 26-34, 35-49; "
             f"{n_obs:,} cells, {n_cl} occupation clusters. Poisson PML with occupation x age, occupation x month",
             "and age x month fixed effects; CRV1 by occupation. Treatment from 2022-12. Label: causal only under the",
             "assumptions in docs/identification.md, and only if the Phase 9 tests do not overturn it.", "",
             "## Headline (Section 11)", "",
             f"**{verdict(h.b, h.lo, h.hi, '22-25-year-olds in Q5 occupations, relative to Q1 and to ages 35-49')}**", "",
             f"- Coefficient {h.b:+.4f} (SE {h.se:.4f}), p = {h.p:.3f}.",
             f"- TOST against ±5% (alpha 0.025 per side, normal approximation): p = {t_lo:.3f} (lower bound), "
             f"{t_hi:.3f} (upper bound); equivalence {'established' if max(t_lo, t_hi) < 0.025 else 'not established'}.",
             f"- Pre-trend rule (Section 11): joint test of the {k_pre} pre-period Q5 x 22-25 bins p = {p_joint:.3f}; "
             f"pre bins with a CI beyond ±5%: {len(beyond)}. Pre-trend {'FLAGGED' if flagged else 'not flagged'}.", ""]
    if flagged:
        lines += ["**Warning (Section 11):** a pre-trend is flagged, so the main result is reported with this warning and",
                  "the sensitivity analysis (Section 13, Phase 9) becomes the main basis for interpretation.", ""]
    lines += ["## All main-model terms (relative to Q1 and ages 35-49)", "",
              "| Term | Quintile | Age | Coefficient | SE | % change (95% CI) | p |", "|---|---|---|---|---|---|---|"]
    for t, r in ct.iterrows():
        lines.append(f"| `{t}` | Q{t[1]} | {'22-25' if t.endswith('22') else '26-34'} | {r.b:+.4f} | {r.se:.4f} | "
                     f"{pct(r.b)} ({pct(r.lo)} to {pct(r.hi)}) | {r.p:.3f} |")
    lines += ["", "## Event study, Q5 x 22-25 (Section 9)", "", "Figure: `results/figures/phase8_event_study.png`.", "",
              "| Bin start | % change (95% CI) |", "|---|---|"]
    lines += [f"| {bin_start(r.bin):%Y-%m} | {pct(r.b)} ({pct(r.lo)} to {pct(r.hi)}) |" for _, r in head.iterrows()]
    lines += ["", "## Secondary outcomes, Q5 x 22-25 (Section 6; Holm within family, Section 10)", "",
              "| Outcome | Coefficient (units) | 95% CI | p | Holm p |", "|---|---|---|---|---|"]
    for k, r in sec.items():
        lines.append(f"| {k} | {r.b:+.3f} | {r.lo:+.3f} to {r.hi:+.3f} | {r.p:.3f} | {holm_p[k]:.3f} |")
    lines += ["", "## L3 (exploratory): Q5 vs Q1 within one age group", "",
              "Poisson PML within each age group, occupation and month fixed effects, CRV1. Exploratory; not preregistered.", "",
              "| Age group | Q5 x post, % change (95% CI) | p |", "|---|---|---|"]
    for a, r in l3.items():
        lines.append(f"| {a} | {pct(r.b)} ({pct(r.lo)} to {pct(r.hi)}) | {r.p:.3f} |")
    TABLE.write_text("\n".join(lines + [""]), encoding="utf-8")
    record("phase8_main", {
        "headline": {**est(h), "verdict": verdict(h.b, h.lo, h.hi, "22-25-year-olds in Q5 occupations, relative to Q1 and to ages 35-49"),
                     "verdict_label": verdict(h.b, h.lo, h.hi, "").split(":")[0],
                     "tost_p_lower": round(t_lo, 4), "tost_p_upper": round(t_hi, 4)},
        "pretrend": {"joint_p": round(p_joint, 4), "bins_beyond_5pct": len(beyond), "flagged": bool(flagged)},
        "terms": {t: est(r) for t, r in ct.iterrows()},
        "event_study_q5_a22": {f"{bin_start(r.bin):%Y-%m}": est(r) for _, r in head.iterrows()},
        "secondary_q5_a22": {k: {"coef": round(float(r.b), 3), "lo": round(float(r.lo), 3), "hi": round(float(r.hi), 3),
                                 "p": round(float(r.p), 4), "holm_p": round(holm_p[k], 4)} for k, r in sec.items()},
        "l3_within_age_q5_vs_q1": {a: est(r) for a, r in l3.items()},
        "n_cells": int(n_obs), "n_clusters": int(n_cl)})
    print("\n".join(lines))


if __name__ == "__main__":
    assert verdict(-0.2, -0.3, -0.1, "g").startswith("Effect detected")
    assert verdict(0.0, -0.02, 0.02, "g").startswith("No meaningful effect")
    assert "differs from zero" in verdict(-0.06, -0.10, -0.01, "g")
    assert holm({"a": 0.01, "b": 0.04, "c": 0.03}) == {"a": 0.03, "c": 0.06, "b": 0.06}
    main()
