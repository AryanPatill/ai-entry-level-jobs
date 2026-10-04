"""Phase 5: build the analysis panel (preregistration Sections 4 and 8) and the cell-size report.

Unit: occupation (OCC2010) x age group x month. Sample (Section 4):
  - Armed Forces dropped (EMPSTAT = 1; all have WTFINL = 0)
  - employed, including employed but absent (EMPSTAT 10, 12)
  - wage and salary only: CLASSWKR in settings.design.wage_salary_classwkr
  - ages 22-64 in the four preregistered groups
  - occupations with an exposure quintile (frozen cutoffs, results/tables/exposure_quintile_cutoffs.csv)
The panel is balanced: every scored occupation x age group x month, zeros filled, because
the Poisson model (Section 8) needs the zero cells. All months 2011-01 to 2026-08 are kept,
with flags; excluded months are dropped at estimation time, not here.

The panel holds the outcome (weighted counts) and is written to data/processed/, never
committed and never printed. The report shows unweighted record counts only, summarised
so no trend is visible (no month-by-month table).

Run from the repo root:  python -m src.data.build_panel
"""
from __future__ import annotations

import duckdb
import pandas as pd

from src.crosswalks.exposure_quintiles import occupation_quintiles
from src.crosswalks.occupation_exposure import cps_parquet
from src.utils.config import REPO_ROOT, load_settings

AGE_GROUPS = {"22-25": "treated_ages", "26-34": "secondary_ages",
              "35-49": "comparison_ages", "50-64": "placebo_ages"}
REPORT_FILE = REPO_ROOT / "results" / "tables" / "cell_sizes.md"


def ym(month: str) -> int:
    return int(month.replace("-", ""))


def main() -> None:
    s = load_settings()
    d = s["design"]
    src = f"read_parquet('{cps_parquet()}')"
    ws = ", ".join(str(c) for c in d["wage_salary_classwkr"])
    age_case = " ".join(f"WHEN AGE BETWEEN {d[k][0]} AND {d[k][1]} THEN '{g}'" for g, k in AGE_GROUPS.items())
    con = duckdb.connect()

    # Sample flow: records at each step, pooled over all months and ages.
    flow = con.execute(f"""SELECT COUNT(*),
        COUNT(*) FILTER (WHERE EMPSTAT <> 1),
        COUNT(*) FILTER (WHERE EMPSTAT IN (10, 12)),
        COUNT(*) FILTER (WHERE EMPSTAT IN (10, 12) AND CLASSWKR IN ({ws}))
        FROM {src}""").fetchone()

    occ = occupation_quintiles()
    con.register("occ", occ)
    cells = con.execute(f"""
        SELECT p.OCC2010 AS occ2010, CASE {age_case} END AS age_group, p.YEAR * 100 + p.MONTH AS ym,
               SUM(p.WTFINL) AS emp_w, COUNT(*) AS n_records
        FROM {src} p JOIN occ o ON p.OCC2010 = o.occ2010
        WHERE p.EMPSTAT <> 1 AND p.EMPSTAT IN (10, 12) AND p.CLASSWKR IN ({ws})
        GROUP BY 1, 2, 3""").df()
    in_scored = int(cells["n_records"].sum())

    months = sorted(con.execute(f"SELECT DISTINCT YEAR * 100 + MONTH FROM {src}").df().iloc[:, 0])
    grid = pd.MultiIndex.from_product([sorted(cells.occ2010.unique()), list(AGE_GROUPS), months],
                                      names=["occ2010", "age_group", "ym"]).to_frame(index=False)
    panel = grid.merge(cells, how="left").fillna({"emp_w": 0.0, "n_records": 0})
    panel["n_records"] = panel["n_records"].astype(int)
    panel = panel.merge(occ[["occ2010", "quintile"]], on="occ2010")
    panel["pandemic"] = panel.ym.between(ym(d["excluded_start"]), ym(d["excluded_end"]))
    panel["main_sample"] = (panel.ym >= ym(d["main_start"])) & ~panel.pandemic
    panel["post"] = panel.ym >= ym(d["treatment_month"])

    out = s["paths"]["processed"] / "panel_occ_age_month.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out, index=False)
    print(f"Wrote {out.relative_to(REPO_ROOT)}: {len(panel):,} cells (outcome not printed)")

    # Hours outcome exclusions (Section 6): share of the panel sample NOT in the hours outcome,
    # by reason, age group and period. A shift in these shares would bias mean hours.
    h0, h1 = d["hours_range"]
    he = ", ".join(map(str, d["hours_empstat"]))
    period = (f"CASE WHEN ym BETWEEN {ym(d['excluded_start'])} AND {ym(d['excluded_end'])} THEN NULL "
              f"WHEN ym < {ym(d['main_start'])} THEN NULL WHEN ym < {ym(d['treatment_month'])} THEN 'pre' ELSE 'post' END")
    hours = con.execute(f"""
        WITH x AS (SELECT CASE {age_case} END AS age_group, YEAR * 100 + MONTH AS ym, WTFINL AS w,
                          EMPSTAT NOT IN ({he}) AS absent, UHRSWORK1 AS h
                   FROM {src} p JOIN occ o ON p.OCC2010 = o.occ2010
                   WHERE p.EMPSTAT IN (10, 12) AND p.CLASSWKR IN ({ws}))
        SELECT age_group, {period} AS period,
               SUM(w * absent::INT) / SUM(w) AS absent,
               SUM(w * (NOT absent AND h = 997)::INT) / SUM(w) AS vary,
               SUM(w * (NOT absent AND h = 0)::INT) / SUM(w) AS zero,
               SUM(w * (NOT absent AND h <> 997 AND h <> 0 AND NOT h BETWEEN {h0} AND {h1})::INT) / SUM(w) AS other,
               SUM(w * (absent OR NOT h BETWEEN {h0} AND {h1})::INT) / SUM(w) AS total
        FROM x GROUP BY 1, 2 HAVING period IS NOT NULL ORDER BY 1, 2 DESC""").df()

    REPORT_FILE.write_text(report(flow, in_scored, panel, d) + hours_report(hours, d), encoding="utf-8")
    print(f"Wrote {REPORT_FILE.relative_to(REPO_ROOT)}")


def report(flow, in_scored: int, panel: pd.DataFrame, d: dict) -> str:
    m = panel[panel.main_sample]
    lines = [
        "# Cell sizes (Phase 5; preregistration Section 16)",
        "",
        "Generated by `python -m src.data.build_panel`. Unweighted record counts only. Summarised",
        f"over the main-sample months ({d['main_start']} onward, {d['excluded_start']} to "
        f"{d['excluded_end']} excluded, {m.ym.nunique()} months), with no month-by-month table,",
        "no pre/post split and no weights, so no trend is visible.",
        "",
        "## Sample flow (records, all months and ages pooled)",
        "",
        "| Step | Records |", "|---|---|",
        f"| Extract (ages 22-64) | {flow[0]:,} |",
        f"| Drop Armed Forces (EMPSTAT = 1) | {flow[1]:,} |",
        f"| Employed (EMPSTAT 10, 12) | {flow[2]:,} |",
        f"| Wage and salary (CLASSWKR {', '.join(map(str, d['wage_salary_classwkr']))}) | {flow[3]:,} |",
        f"| Occupation has an exposure quintile | {in_scored:,} |",
        "",
        "## Records per age group x quintile x month (main-sample months)",
        "",
        "| Age group | Quintile | Min | 10th pct | Median |", "|---|---|---|---|---|",
    ]
    aq = m.groupby(["age_group", "quintile", "ym"])["n_records"].sum().groupby(["age_group", "quintile"])
    for (a, q), x in aq:
        lines.append(f"| {a} | Q{q} | {x.min():,} | {x.quantile(0.1):,.0f} | {x.median():,.0f} |")
    lines += ["", "## Model cells: occupation x age group x month (main-sample months)", "",
              f"{m.occ2010.nunique()} occupations x {m.age_group.nunique()} age groups x "
              f"{m.ym.nunique()} months = {len(m):,} cells.", "",
              "| Age group | Quintile | Occupations | Cells with 0 records | 1-4 | 5-9 |",
              "|---|---|---|---|---|---|"]
    for (a, q), x in m.groupby(["age_group", "quintile"]):
        n = x.n_records
        lines.append(f"| {a} | Q{q} | {x.occ2010.nunique()} | {(n == 0).mean():.1%} | "
                     f"{n.between(1, 4).mean():.1%} | {n.between(5, 9).mean():.1%} |")
    lines.append("")
    return "\n".join(lines)


def hours_report(h: pd.DataFrame, d: dict) -> str:
    lines = ["## Hours outcome exclusions (Section 6)", "",
             f"Share of employed wage and salary workers in scored occupations NOT in the mean-hours",
             f"outcome (kept: EMPSTAT {d['hours_empstat']}, UHRSWORK1 {d['hours_range'][0]}-{d['hours_range'][1]}).",
             f"Weighted by WTFINL. Pre = {d['main_start']} to the month before {d['treatment_month']}, "
             f"pandemic months excluded; post = {d['treatment_month']} on.", "",
             "| Age group | Period | Absent (EMPSTAT 12) | Hours vary (997) | 0 hours | Other | Total excluded |",
             "|---|---|---|---|---|---|---|"]
    for r in h.itertuples():
        lines.append(f"| {r.age_group} | {r.period} | {r.absent:.1%} | {r.vary:.1%} | {r.zero:.2%} | "
                     f"{r.other:.2%} | {r.total:.1%} |")
    return "\n".join(lines + [""])


if __name__ == "__main__":
    main()
