"""Phase 5: build the analysis panel (preregistration Sections 4 and 8) and the cell-size report.

Unit: occupation (OCC2010) x age group x month. Sample (Section 4):
  - Armed Forces dropped (EMPSTAT = 1; all have WTFINL = 0)
  - employed, including employed but absent (EMPSTAT 10, 12)
  - wage and salary only: CLASSWKR in settings.design.wage_salary_classwkr
  - ages 22-64 in the four preregistered groups
  - occupations with an exposure quintile (frozen cutoffs, results/tables/exposure_quintile_cutoffs.csv)
Outcome sums per cell (rates and means are formed at estimation, never here):
  emp_w / n_records   employed, weighted / records (primary outcome, Section 6)
  unemp_w / n_unemp   experienced unemployed placed by last occupation, wage and salary last job
  hours_w, hours_wsum weight and weight x UHRSWORK1 for the hours outcome (EMPSTAT 10, 1-168)
  emp_w_ba, emp_w_men, emp_w_women, emp_w_private, emp_w_fulltime   subgroup / robustness samples
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
    un = ", ".join(map(str, d["unemployed_empstat"]))
    he = ", ".join(map(str, d["hours_empstat"]))
    h0, h1 = d["hours_range"]
    emp = "p.EMPSTAT IN (10, 12)"
    hrs = f"p.EMPSTAT IN ({he}) AND p.UHRSWORK1 BETWEEN {h0} AND {h1}"
    # Sums only; rates and means are formed at estimation (Phase 8), never here.
    cells = con.execute(f"""
        SELECT p.OCC2010 AS occ2010, CASE {age_case} END AS age_group, p.YEAR * 100 + p.MONTH AS ym,
               SUM(p.WTFINL) FILTER (WHERE {emp})                       AS emp_w,
               COUNT(*) FILTER (WHERE {emp})                            AS n_records,
               SUM(p.WTFINL) FILTER (WHERE p.EMPSTAT IN ({un}))         AS unemp_w,
               COUNT(*) FILTER (WHERE p.EMPSTAT IN ({un}))              AS n_unemp,
               SUM(p.WTFINL) FILTER (WHERE {hrs})                       AS hours_w,
               SUM(p.WTFINL * p.UHRSWORK1) FILTER (WHERE {hrs})         AS hours_wsum,
               SUM(p.WTFINL) FILTER (WHERE {emp} AND p.EDUC IN ({', '.join(map(str, d['ba_plus_educ']))})) AS emp_w_ba,
               SUM(p.WTFINL) FILTER (WHERE {emp} AND p.SEX = 1)         AS emp_w_men,
               SUM(p.WTFINL) FILTER (WHERE {emp} AND p.SEX = 2)         AS emp_w_women,
               SUM(p.WTFINL) FILTER (WHERE {emp} AND p.CLASSWKR IN ({', '.join(map(str, d['private_classwkr']))})) AS emp_w_private,
               SUM(p.WTFINL) FILTER (WHERE {emp} AND p.UHRSWORK1 BETWEEN {d['fulltime_min_hours']} AND {h1}) AS emp_w_fulltime
        FROM {src} p JOIN occ o ON p.OCC2010 = o.occ2010
        WHERE p.EMPSTAT <> 1 AND (p.EMPSTAT IN (10, 12) OR p.EMPSTAT IN ({un})) AND p.CLASSWKR IN ({ws})
        GROUP BY 1, 2, 3""").df()
    in_scored, n_unemp = int(cells["n_records"].sum()), int(cells["n_unemp"].sum())

    months = sorted(con.execute(f"SELECT DISTINCT YEAR * 100 + MONTH FROM {src}").df().iloc[:, 0])
    occs = sorted(cells.loc[cells.n_records > 0, "occ2010"].unique())   # occupations with any employment
    grid = pd.MultiIndex.from_product([occs, list(AGE_GROUPS), months],
                                      names=["occ2010", "age_group", "ym"]).to_frame(index=False)
    panel = grid.merge(cells, how="left")
    sums = [c for c in cells.columns if c not in ("occ2010", "age_group", "ym")]
    panel[sums] = panel[sums].fillna(0)
    panel[["n_records", "n_unemp"]] = panel[["n_records", "n_unemp"]].astype(int)
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

    REPORT_FILE.write_text(report(flow, in_scored, n_unemp, panel, d) + hours_report(hours, d), encoding="utf-8")
    print(f"Wrote {REPORT_FILE.relative_to(REPO_ROOT)}")


def report(flow, in_scored: int, n_unemp: int, panel: pd.DataFrame, d: dict) -> str:
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
        f"| Also in the panel: unemployed (EMPSTAT {d['unemployed_empstat']}), wage and salary last job, "
        f"last occupation has a quintile | {n_unemp:,} |",
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
