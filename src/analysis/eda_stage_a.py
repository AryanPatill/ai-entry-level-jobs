"""Phase 6, Stage A: data-quality checks before any outcome trend is shown. DESCRIPTIVE.

A1  Records per month, everyone in the extract pooled (sample size, not an outcome).
A2  Threat 6 (Section 12): employment per occupation, all ages pooled, Dec 2019 vs Jan 2020
    (the occupation code change). Benchmark: the same occupations' Dec -> Jan changes in
    2015-2019. Flag: |log change| beyond the benchmark's 99th percentile, among occupations
    with >= MIN_RECORDS records in both months. With no code-change effect about 1% are flagged.
A3  "Hours vary" (UHRSWORK1 997) share among at-work wage and salary workers, by quintile x
    period, ages pooled (commitment in plan.md). A measurement variable, not an outcome.

Run from the repo root:  python -m src.analysis.eda_stage_a
"""
from __future__ import annotations

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ipumspy import readers

from src.crosswalks.exposure_quintiles import occupation_quintiles
from src.crosswalks.occupation_exposure import cps_parquet
from src.data.build_panel import ym
from src.data.convert_to_parquet import locate_files
from src.data.inspect_codes import labels_for
from src.data.ipums_extract import load_log
from src.utils.config import REPO_ROOT, load_settings

MIN_RECORDS = 50
REF_TRANSITIONS = [(201512, 201601), (201612, 201701), (201712, 201801), (201812, 201901)]
TABLE = REPO_ROOT / "results" / "tables" / "phase6_stage_a.md"
FIG = REPO_ROOT / "results" / "figures" / "a1_records_per_month.png"
INK, INK2, SERIES, SURFACE = "#0b0b0b", "#52514e", "#2a78d6", "#fcfcfb"   # dataviz reference palette


def a1(con, src) -> list[str]:
    r = con.execute(f"SELECT YEAR * 100 + MONTH AS ym, COUNT(*) AS n FROM {src} GROUP BY 1 ORDER BY 1").df()
    full = pd.DataFrame({"ym": [y * 100 + m for y in range(2011, 2027) for m in range(1, 13) if y * 100 + m <= r.ym.max()]})
    r = full.merge(r, how="left")   # 2025-10 stays NaN, so the line breaks there
    dates = pd.to_datetime(r.ym.astype(str), format="%Y%m")

    fig, ax = plt.subplots(figsize=(9, 3.6), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot(dates, r.n / 1000, color=SERIES, lw=2)
    nov = r.loc[r.ym == 202511]
    ax.plot(pd.to_datetime("2025-11"), nov.n.iloc[0] / 1000, "o", ms=8, color=SERIES, mec=SURFACE, mew=2)
    ax.annotate("Oct 2025 not collected\nNov 2025 collected late", (pd.to_datetime("2025-11"), nov.n.iloc[0] / 1000),
                xytext=(-150, -38), textcoords="offset points", color=INK2, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.set_title("DESCRIPTIVE. CPS records per month, ages 22-64, all respondents", loc="left", color=INK, fontsize=11)
    ax.set_ylabel("Records (thousands)", color=INK2)
    ax.set_ylim(0, None)
    ax.grid(axis="y", color="#e6e5e0", lw=0.8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, length=0)
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=150)

    around = r[r.ym.isin([202508, 202509, 202511, 202512, 202601])].dropna()
    return ["## A1. Records per month (sample size, not an outcome)", "",
            f"Figure: `results/figures/{FIG.name}`. 2025-10 is absent (never collected).", "",
            "| Month | Records |", "|---|---|",
            *[f"| {int(m) // 100}-{int(m) % 100:02d} | {int(n):,} |" for m, n in zip(around.ym, around.n)], ""]


def a2(panel: pd.DataFrame, labels: dict) -> list[str]:
    occ = panel.groupby(["occ2010", "ym"])[["emp_w", "n_records"]].sum().reset_index()

    def change(m0, m1):
        a = occ[occ.ym == m0].set_index("occ2010")
        b = occ[occ.ym == m1].set_index("occ2010")
        j = a.join(b, lsuffix="_0", rsuffix="_1", how="inner")
        j = j[(j.n_records_0 >= MIN_RECORDS) & (j.n_records_1 >= MIN_RECORDS)]
        return np.log(j.emp_w_1 / j.emp_w_0), j

    ref = pd.concat([change(*t)[0] for t in REF_TRANSITIONS])
    cut = ref.abs().quantile(0.99)
    lr, j = change(201912, 202001)
    flagged = lr[lr.abs() > cut].sort_values(key=abs, ascending=False)
    small = occ[(occ.ym.isin([201912, 202001]))].groupby("occ2010").n_records.min()
    lines = ["## A2. Occupation code change, Dec 2019 to Jan 2020 (threat 6)", "",
             "Weighted employment per OCC2010 code, all ages pooled. Benchmark: the same occupations' Dec to",
             f"Jan log changes in 2015-2019 ({len(ref):,} occupation-transitions). Flag: |log change| above",
             f"the benchmark's 99th percentile ({cut:.3f}), among occupations with at least {MIN_RECORDS} records in",
             "both months. If the code change had no effect, about 1% would be flagged.", "",
             f"- Occupations checked: {len(lr)}; flagged: {len(flagged)} ({len(flagged) / len(lr):.1%}).",
             f"- Benchmark years beyond the same cutoff: 1.0% by construction.",
             f"- Occupations below {MIN_RECORDS} records in either month (not checked): {(small < MIN_RECORDS).sum()}.",
             "", "| OCC2010 | IPUMS label | Log change | Records Dec 2019 | Records Jan 2020 |", "|---|---|---|---|---|"]
    for c, v in flagged.items():
        lines.append(f"| {c:04d} | {labels.get(c, '')} | {v:+.3f} | {int(j.loc[c, 'n_records_0']):,} | "
                     f"{int(j.loc[c, 'n_records_1']):,} |")
    return lines + [""]


def a3(con, src, d) -> list[str]:
    ws = ", ".join(map(str, d["wage_salary_classwkr"]))
    period = (f"CASE WHEN m BETWEEN {ym(d['excluded_start'])} AND {ym(d['excluded_end'])} OR m < {ym(d['main_start'])} "
              f"THEN NULL WHEN m < {ym(d['treatment_month'])} THEN 'pre' ELSE 'post' END")
    h = con.execute(f"""
        WITH x AS (SELECT o.quintile, YEAR * 100 + MONTH AS m, WTFINL AS w, (UHRSWORK1 = 997)::INT AS vary
                   FROM {src} p JOIN occ o ON p.OCC2010 = o.occ2010
                   WHERE p.EMPSTAT = 10 AND p.CLASSWKR IN ({ws}))
        SELECT quintile, {period} AS period, SUM(w * vary) / SUM(w) AS share
        FROM x GROUP BY 1, 2 HAVING period IS NOT NULL""").df()
    t = h.pivot(index="quintile", columns="period", values="share")
    lines = ["## A3. \"Hours vary\" share by quintile x period (measurement variable, not an outcome)", "",
             "Weighted share of at-work (EMPSTAT 10) wage and salary workers reporting UHRSWORK1 = 997, ages",
             f"pooled. Pre = {d['main_start']} to before {d['treatment_month']}, pandemic months excluded; post = "
             f"{d['treatment_month']} on.", "",
             "| Quintile | Pre | Post | Change (points) |", "|---|---|---|---|"]
    for q, r in t.iterrows():
        lines.append(f"| Q{q} | {r['pre']:.1%} | {r['post']:.1%} | {100 * (r['post'] - r['pre']):+.1f} |")
    return lines + [""]


def main() -> None:
    d = load_settings()["design"]
    src = f"read_parquet('{cps_parquet()}')"
    con = duckdb.connect()
    con.register("occ", occupation_quintiles())
    panel = pd.read_parquet(load_settings()["paths"]["processed"] / "panel_occ_age_month.parquet",
                            columns=["occ2010", "ym", "emp_w", "n_records"])
    labels = labels_for(readers.read_ipums_ddi(locate_files(load_log())[2]), "OCC2010")
    lines = ["# Phase 6, Stage A: data-quality checks. DESCRIPTIVE", "",
             "Generated by `python -m src.analysis.eda_stage_a`. No age x exposure outcome trend appears here.", "",
             *a1(con, src), *a2(panel, labels), *a3(con, src, d)]
    TABLE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
