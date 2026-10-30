"""Phase 6: two open checks before Stage C. DESCRIPTIVE; no age x exposure view.

1. Do the occupations flagged at the 2020 code change (Stage A, A2) cluster in a quintile?
2. What drives the Q2 jump between the Dec 2024 and Mar 2025 bins (Stage B, B2)?
   Monthly Q2 employment, ages pooled, weighted and as raw records; Q2's share of the total
   both ways (a jump in the weighted share only points to weights, not people); the Q2
   occupations behind the change; and whether raw OCC codes changed between 2024 and 2025.

Run from the repo root:  python -m src.analysis.eda_open_checks
"""
from __future__ import annotations

import duckdb
import pandas as pd
from ipumspy import readers

from src.analysis.eda_stage_a import a2_flags
from src.crosswalks.occupation_exposure import cps_parquet
from src.data.convert_to_parquet import locate_files
from src.data.inspect_codes import labels_for
from src.data.ipums_extract import load_log
from src.utils.config import REPO_ROOT, load_settings

TABLE = REPO_ROOT / "results" / "tables" / "phase6_open_checks.md"
BIN_DEC24, BIN_MAR25 = [202412, 202501, 202502], [202503, 202504, 202505]


def check1(panel: pd.DataFrame) -> list[str]:
    lr, flagged, *_ = a2_flags(panel)
    q = panel.drop_duplicates("occ2010").set_index("occ2010").quintile
    checked, flg = q.loc[lr.index].value_counts().sort_index(), q.loc[flagged.index].value_counts()
    lines = ["## 1. Do the 2020 code-change flags cluster in a quintile?", "",
             f"{len(flagged)} flagged of {len(lr)} occupations checked (Stage A, A2). Codes only.", "",
             "| Quintile | Occupations checked | Flagged | Flagged codes |", "|---|---|---|---|"]
    for k, n in checked.items():
        codes = ", ".join(f"{c:04d}" for c in flagged.index if q[c] == k)
        lines.append(f"| Q{k} | {n} | {flg.get(k, 0)} | {codes} |")
    return lines + [""]


def check2(panel: pd.DataFrame, labels: dict) -> list[str]:
    win = panel[panel.ym.between(202409, 202508)]
    m = win.assign(q2=win.quintile == 2).groupby(["ym", "q2"])[["emp_w", "n_records"]].sum().unstack()
    lines = ["## 2. The Q2 jump between the Dec 2024 and Mar 2025 bins", "",
             "Q2 employment by month, ages pooled; Q2 share of all scored employment, weighted and by records.", "",
             "| Month | Q2 weighted (M) | Q2 records | Q2 share, weighted | Q2 share, records |", "|---|---|---|---|---|"]
    for ym_, r in m.iterrows():
        w, n = r["emp_w"], r["n_records"]
        lines.append(f"| {ym_ // 100}-{ym_ % 100:02d} | {w[True] / 1e6:.2f} | {int(n[True]):,} | "
                     f"{w[True] / w.sum():.2%} | {n[True] / n.sum():.2%} |")

    q2 = panel[panel.quintile == 2]
    avg = lambda months: q2[q2.ym.isin(months)].groupby("occ2010")[["emp_w", "n_records"]].sum() / len(months)
    a, b = avg(BIN_DEC24), avg(BIN_MAR25)
    d = (b.emp_w - a.emp_w).sort_values(key=abs, ascending=False)
    lines += ["", f"Q2 occupations with the largest change in average monthly weighted employment, Dec 2024-Feb 2025 "
              f"to Mar-May 2025 (total Q2 change {d.sum() / 1e6:+.2f}M):", "",
              "| OCC2010 | IPUMS label | Change (thousands) | Records/month before | Records/month after |",
              "|---|---|---|---|---|"]
    for c in d.index[:8]:
        lines.append(f"| {c:04d} | {labels.get(c, '')} | {d[c] / 1e3:+,.0f} | {a.n_records.get(c, 0):,.0f} | "
                     f"{b.n_records.get(c, 0):,.0f} |")

    # Is it usual? The same two transitions in other years, as changes in Q2's share (points).
    def share(months):
        x = panel[panel.ym.isin(months)]
        return (100 * x.loc[x.quintile == 2, "emp_w"].sum() / x.emp_w.sum(),
                100 * x.loc[x.quintile == 2, "n_records"].sum() / x.n_records.sum())
    lines += ["", "Change in Q2's share (points), same transitions in other years. Dec -> Jan isolates the January",
              "weight revision; Dec-Feb -> Mar-May is the bin step seen in B2.", "",
              "| Year | Dec -> Jan, weighted | Dec -> Jan, records | Dec-Feb -> Mar-May, weighted | Dec-Feb -> Mar-May, records |",
              "|---|---|---|---|---|"]
    for y in (2016, 2017, 2018, 2019, 2023, 2024, 2025, 2026):
        dec, jan = share([(y - 1) * 100 + 12]), share([y * 100 + 1])
        w0, w1 = share([(y - 1) * 100 + 12, y * 100 + 1, y * 100 + 2]), share([y * 100 + 3, y * 100 + 4, y * 100 + 5])
        lines.append(f"| {y} | {jan[0] - dec[0]:+.2f} | {jan[1] - dec[1]:+.2f} | {w1[0] - w0[0]:+.2f} | {w1[1] - w0[1]:+.2f} |")
    return lines + [""]


def check2_codes() -> list[str]:
    src = f"read_parquet('{cps_parquet()}')"
    con = duckdb.connect()
    sets = {y: {r[0] for r in con.execute(f"SELECT DISTINCT OCC FROM {src} WHERE YEAR = {y}").fetchall()}
            for y in (2023, 2024, 2025)}
    h = {y: {r[0] for r in con.execute(f"SELECT DISTINCT OCC2010 FROM {src} WHERE YEAR = {y}").fetchall()}
         for y in (2023, 2024, 2025)}
    return ["Raw occupation codes (codes only):", "",
            f"- OCC distinct codes: 2023 {len(sets[2023])}, 2024 {len(sets[2024])}, 2025 {len(sets[2025])}; "
            f"2024 and 2025 share {len(sets[2024] & sets[2025])}; only in 2025: {len(sets[2025] - sets[2024])}; "
            f"only in 2024: {len(sets[2024] - sets[2025])}.",
            f"- Same comparison 2023 to 2024: shared {len(sets[2023] & sets[2024])}; only in 2024: "
            f"{len(sets[2024] - sets[2023])}; only in 2023: {len(sets[2023] - sets[2024])}.",
            f"- OCC2010 codes only in 2025: {sorted(h[2025] - h[2024]) or 'none'}; only in 2024: "
            f"{sorted(h[2024] - h[2025]) or 'none'}.", ""]


def main() -> None:
    panel = pd.read_parquet(load_settings()["paths"]["processed"] / "panel_occ_age_month.parquet",
                            columns=["occ2010", "ym", "quintile", "emp_w", "n_records"])
    labels = labels_for(readers.read_ipums_ddi(locate_files(load_log())[2]), "OCC2010")
    lines = ["# Phase 6: open checks before Stage C. DESCRIPTIVE", "",
             "Generated by `python -m src.analysis.eda_open_checks`. Ages pooled throughout; no age x exposure view.", "",
             *check1(panel), *check2(panel, labels), *check2_codes()]
    TABLE.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
