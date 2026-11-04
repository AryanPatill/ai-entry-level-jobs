"""Phase 9: robustness and falsification for the headline (Sections 12, 13; identification.md).

Each row refits the Section 8 model with one change and reports the headline term (Q5 x focal age x post).
Preregistered rows follow Sections 12-13; rows marked exploratory come from identification.md 7.4.
Section 12's reading rule: a shrinking estimate under T1-T3 controls means the design cannot separate AI
from that threat, not that AI had no effect.

Run from the repo root:  python -m src.analysis.robustness
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyfixest as pf

from src.analysis.eda_stage_a import a2_flags
from src.analysis.estimate_main import FE, VCOV, coef_table, event_study, pct, verdict
from src.crosswalks.exposure_quintiles import occupation_quintiles
from src.utils.config import REPO_ROOT, load_settings

TABLE = REPO_ROOT / "results" / "tables" / "phase9_robustness.md"
YOUNG = ("22-25", "26-34")


def terms(p: pd.DataFrame, post: pd.Series, ages=YOUNG, prefix="q") -> list[str]:
    out = []
    for q in (2, 3, 4, 5):
        for a in ages:
            n = f"{prefix}{q}_a{a[:2]}"
            p[n] = ((p.quintile == q) & (p.age_group == a)).astype(int) * post.astype(int)
            out.append(n)
    return out


def fit(p: pd.DataFrame, y: str = "emp_w", treat: int = 202212, ages=YOUNG, extra: list[str] | None = None,
        fe: str = FE) -> pd.Series:
    p = p.copy()
    t = terms(p, p.ym >= treat, ages)
    f = pf.fepois(f"{y} ~ {' + '.join(t + (extra or []))} | {fe}", data=p, vcov=VCOV)
    return coef_table(f, t).loc[f"q5_a{ages[0][:2]}"]


def main() -> None:
    s = load_settings()
    d = s["design"]
    proc = s["paths"]["processed"]
    full = pd.read_parquet(proc / "panel_occ_age_month.parquet")
    three = full[full.age_group.isin(["22-25", "26-34", "35-49"])]
    main_p = three[three.main_sample]
    rows = []

    def add(label, sec, kind, r):
        rows.append((label, sec, kind, r))
        print(f"{label}: {pct(r.b)} ({pct(r.lo)} to {pct(r.hi)})", flush=True)

    add("Main specification (Phase 8)", "8", "preregistered", fit(main_p))
    for m in d["alternative_treatment_months"]:
        add(f"Treatment date {m}", "13", "preregistered", fit(main_p, treat=int(m.replace("-", ""))))
    add("Start in 2011-01", "13", "preregistered", fit(three[(three.ym >= 201101) & ~three.pandemic]))

    pk = three[three.ym >= 201501].copy()
    extra = []
    for q in (2, 3, 4, 5):
        for a in YOUNG:
            pk[f"pan{q}_{a[:2]}"] = ((pk.quintile == q) & (pk.age_group == a) & pk.pandemic).astype(int)
            extra.append(f"pan{q}_{a[:2]}")
    add("Pandemic months kept, quintile x age x pandemic indicators", "13; T5", "preregistered", fit(pk, extra=extra))

    # Continuous exposure: exposure (sd units) x age x post, Q terms replaced.
    ex = occupation_quintiles().set_index("occ2010").exposure
    c = main_p.copy()
    c["z"] = c.occ2010.map((ex - ex.mean()) / ex.std())
    cterms = []
    for a in YOUNG:
        c[f"z_a{a[:2]}"] = c.z * (c.age_group == a) * c.post
        cterms.append(f"z_a{a[:2]}")
    fc = pf.fepois(f"emp_w ~ {' + '.join(cterms)} | {FE}", data=c, vcov=VCOV)
    rc = coef_table(fc, cterms).loc["z_a22"]

    add("Private-sector employees only", "13", "preregistered", fit(main_p, y="emp_w_private"))
    add("Full-time workers only", "13", "preregistered", fit(main_p, y="emp_w_fulltime"))
    st = main_p[main_p.student_window].copy()
    st["emp_w_nostud"] = st.emp_w - st.emp_w_student.where(st.age_group == "22-25", 0)
    add("Student filter (enrolled 22-25 removed; 2013-01 on)", "13", "preregistered (deviation 2026-10-17)", fit(st, y="emp_w_nostud"))
    add("Unweighted counts", "13; L2(a)", "preregistered", fit(main_p, y="n_records"))

    b = main_p.copy()
    low = terms(b, pd.Series(True, index=b.index), YOUNG, prefix="qa")          # quintile x age
    for q in (2, 3, 4, 5):
        b[f"qp{q}"] = ((b.quintile == q) & b.post).astype(int)
    for a in YOUNG:
        b[f"ap{a[:2]}"] = ((b.age_group == a) & b.post).astype(int)
    add("Basic fixed effects (occupation, age, month, plus two-way terms)", "13", "preregistered",
        fit(b, extra=low + [f"qp{q}" for q in (2, 3, 4, 5)] + [f"ap{a[:2]}" for a in YOUNG], fe="occ2010 + age_group + ym"))

    # Threat 1: sector panel.
    sp = pd.read_parquet(proc / "panel_occ_sector_age_month.parquet")
    sp = sp[sp.main_sample & sp.age_group.isin(["22-25", "26-34", "35-49"])]
    drop = sp[~sp.sector.isin([1, 2])].groupby(["occ2010", "age_group", "ym"], as_index=False).emp_w.sum()
    drop = drop.merge(main_p[["occ2010", "age_group", "ym", "quintile"]], on=["occ2010", "age_group", "ym"])
    add("T1(a) drop tech and finance (sectors 1, 2)", "12", "preregistered", fit(drop))
    add("T1(b) industry x age x month fixed effects", "12", "preregistered",
        fit(sp, fe="occ2010^sector^age_group + occ2010^ym + sector^age_group^ym"))

    g = pd.read_parquet(s["paths"]["interim"] / "threat_inputs.parquet").set_index("occ2010")
    t2 = main_p[main_p.occ2010.map(g.growth).notna()].copy()
    gx = []
    for a in YOUNG:
        t2[f"g_a{a[:2]}"] = t2.occ2010.map(g.growth) * (t2.age_group == a) * t2.post
        gx.append(f"g_a{a[:2]}")
    add("T2 pre-treatment growth x age x post", "12", "preregistered", fit(t2, extra=gx))
    t3 = main_p[main_p.occ2010.map(g.telework).notna()].copy()
    tx = []
    for a in YOUNG:
        t3[f"t_a{a[:2]}"] = t3.occ2010.map(g.telework) * (t3.age_group == a) * t3.post
        tx.append(f"t_a{a[:2]}")
    add("T3 teleworkability x age x post (Dingel and Neiman)", "12", "preregistered", fit(t3, extra=tx))
    add("T4(b) drop computer and math occupations (default rule)", "12", "preregistered",
        fit(main_p[~main_p.occ2010.map(g.soc15).fillna(False).astype(bool)]))

    pre = three[three.ym.between(201501, 202002)]
    for m in (201712, 201812):
        add(f"T7 placebo date {m // 100}-{m % 100:02d} (2015-01 to 2020-02)", "12", "preregistered", fit(pre, treat=m))
    pg = full[full.main_sample & full.age_group.isin(["50-64", "35-49"])]
    add("Placebo group: ages 50-64 vs 35-49", "12", "preregistered", fit(pg, ages=("50-64",)))

    flagged = set(a2_flags(full)[1].index)
    add("L1 drop the 8 occupations flagged at the 2020 code change", "id. 7.4", "exploratory", fit(main_p[~main_p.occ2010.isin(flagged)]))
    add("L2(b) end the sample at 2024-12", "id. 7.4", "exploratory", fit(main_p[main_p.ym <= 202412]))

    # Pre-pandemic reference bin (Section 9 / 13): event study with base Dec 2019-Feb 2020.
    es, head, p_joint, k, beyond = event_study(main_p.copy(), base=-12)
    post_avg = head[head.bin >= 0].b.mean()

    m0 = rows[0][3]
    lines = ["# Phase 9: robustness and falsification for the headline", "",
             "Generated by `python -m src.analysis.robustness`. Headline term: Q5 x focal age x post, relative to Q1 and",
             "ages 35-49 (placebo group: focal 50-64). Poisson PML, CRV1 by occupation, Section 8 fixed effects unless",
             "stated. Section 12: a shrinking estimate under T1-T3 means AI cannot be separated from that threat, not",
             "that AI had no effect. Verdict wording is Section 11's; it applies formally to the headline and",
             "subgroups, and is shown here as a guide.", "",
             "| Check | Section | Kind | % change (95% CI) | Section 11 reading | Ratio to main |", "|---|---|---|---|---|---|"]
    for label, sec, kind, r in rows:
        v = verdict(r.b, r.lo, r.hi, "g").split(":")[0]
        lines.append(f"| {label} | {sec} | {kind} | {pct(r.b)} ({pct(r.lo)} to {pct(r.hi)}) | {v} | {r.b / m0.b:.2f} |")
    lines += ["", "## Continuous exposure (Section 13)", "",
              f"Exposure in standard-deviation units (across occupations) x 22-25 x post: {pct(rc.b)} per SD "
              f"(95% CI {pct(rc.lo)} to {pct(rc.hi)}), p = {rc.p:.3f}.", "",
              "## Pre-pandemic reference bin, Dec 2019-Feb 2020 (Sections 9, 13; T5)", "",
              f"- Average of the post-period Q5 x 22-25 bin estimates: {pct(post_avg)}.",
              f"- Joint test of the {k} pre-treatment bins (now including 2022): p = {p_joint:.3f}; bins with a CI beyond "
              f"±5%: {len(beyond)}.", "",
              "## Not run (blocked)", "",
              "- Alternative exposure measures (Felten AIOE, Anthropic Economic Index): not acquired.",
              "- HonestDiD sensitivity: Python package unvalidated, not installed (awaits Aryan).",
              "- Wild cluster bootstrap: not required (465 clusters; Section 10 applies it below 50).", ""]
    TABLE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[-20:]))


if __name__ == "__main__":
    main()
