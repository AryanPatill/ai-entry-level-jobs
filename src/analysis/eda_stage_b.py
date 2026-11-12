"""Phase 6, Stage B: first outcome trends, one dimension at a time. DESCRIPTIVE.

B1  Weighted employment by age group, quintiles pooled.
B2  Weighted employment by quintile, age groups pooled.

Main-sample months only (2015-01 onward, 2020-03 to 2021-12 excluded), grouped into the
Section 9 quarterly bins counted from 2022-12 (bin 0 = Dec-Feb). Each bin is the average
monthly employment over its available months. Indexed to bin -1 (Sep-Nov 2022) = 100, the
main event-study reference (approved 2026-10-17). No model, no inference, no causal claim.

Run from the repo root:  python -m src.analysis.eda_stage_b
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.utils.config import REPO_ROOT, load_settings

TABLE = REPO_ROOT / "results" / "tables" / "phase6_stage_b.md"
FIGDIR = REPO_ROOT / "results" / "figures"
INK, INK2, SURFACE, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # dataviz slots 1-5, validated (light)
BASE_BIN = -1


def add_bin(p: pd.DataFrame) -> pd.DataFrame:
    """Section 9 quarterly bin counted from 2022-12 (bin 0 = Dec-Feb, -1 = Sep-Nov 2022)."""
    return p.assign(bin=((p.ym // 100) * 12 + p.ym % 100 - (2022 * 12 + 12)) // 3)


def binned(p: pd.DataFrame, by: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(level, index with bin -1 = 100) of average monthly employment per bin, one column per group."""
    p = add_bin(p)
    months = p.groupby("bin").ym.nunique()
    level = p.groupby(["bin", by]).emp_w.sum().unstack().div(months, axis=0)
    return level, 100 * level / level.loc[BASE_BIN]


def bin_start(b: int) -> pd.Timestamp:
    return pd.Timestamp("2022-12-01") + pd.DateOffset(months=3 * b)


def style(ax) -> None:
    """House chart style: y grid only, no box, quiet ticks."""
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, length=0)


def draw(ax, idx: pd.DataFrame, ref: float = 100, colors=SERIES, ylim=None) -> None:
    """Lines with a pandemic gap, a reference line, a Dec 2022 marker and nudged end labels."""
    full = idx.reindex(range(idx.index.min(), idx.index.max() + 1))   # empty pandemic bins -> gap
    x = [bin_start(b) for b in full.index]
    ax.set_facecolor(SURFACE)
    if ref is not None:
        ax.axhline(ref, color=GRID, lw=1)
    for color, col in zip(colors, full.columns):
        ax.plot(x, full[col], color=color, lw=2)
    if ylim:
        ax.set_ylim(*ylim)
    lo, hi = ax.get_ylim()
    ax.axvline(bin_start(0), color=INK2, lw=0.8, ls=":")
    ax.text(bin_start(0), lo, " Dec 2022", color=INK2, fontsize=8, va="bottom")
    # Direct end labels, nudged apart so none overlap (identity never by colour alone).
    ends = sorted((full[c].dropna().iloc[-1], c) for c in full.columns)
    gap, placed = 0.045 * (hi - lo), []
    for y, c in ends:
        placed.append((max(y, placed[-1][0] + gap) if placed else y, c))
    for y, c in placed:
        ax.annotate(str(c), (x[-1], y), xytext=(8, 0), textcoords="offset points", color=INK, fontsize=9, va="center")
    style(ax)


NOTE = ("Quarterly bins; pandemic months 2020-03 to 2021-12 excluded (gap). Weighted employment, "
        "wage and salary, scored occupations.")


def figure(idx: pd.DataFrame, title: str, name: str, ylabel: str = "Index, Sep-Nov 2022 = 100",
           ref: float = 100, colors=SERIES) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=SURFACE)
    draw(ax, idx, ref, colors)
    ax.set_title(title, loc="left", color=INK, fontsize=11)
    ax.set_ylabel(ylabel, color=INK2)
    ax.text(0, -0.13, NOTE, transform=ax.transAxes, color=INK2, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR / name, dpi=150)


def table(level: pd.DataFrame, idx: pd.DataFrame, heading: str, fig: str) -> list[str]:
    cols = list(idx.columns)
    lines = [heading, "", f"Figure: `results/figures/{fig}`. Base (bin -1, Sep-Nov 2022) average monthly weighted "
             "employment: " + "; ".join(f"{c} {level.loc[BASE_BIN, c] / 1e6:.2f}M" for c in cols) + ".", "",
             "| Bin start | " + " | ".join(map(str, cols)) + " |", "|---" * (len(cols) + 1) + "|"]
    for b, r in idx.iterrows():
        lines.append(f"| {bin_start(b):%Y-%m} | " + " | ".join(f"{v:.1f}" for v in r) + " |")
    return lines + [""]


def main() -> None:
    p = pd.read_parquet(load_settings()["paths"]["processed"] / "panel_occ_age_month.parquet",
                        columns=["age_group", "quintile", "ym", "emp_w", "main_sample"])
    p = p[p.main_sample]
    p["quintile"] = "Q" + p.quintile.astype(str)
    FIGDIR.mkdir(parents=True, exist_ok=True)

    l1, i1 = binned(p, "age_group")
    figure(i1, "DESCRIPTIVE. B1: employment by age group (all quintiles pooled)", "b1_employment_by_age.png")
    l2, i2 = binned(p, "quintile")
    figure(i2, "DESCRIPTIVE. B2: employment by exposure quintile (all ages pooled)", "b2_employment_by_quintile.png")

    lines = ["# Phase 6, Stage B: first outcome trends, one dimension at a time. DESCRIPTIVE", "",
             "Generated by `python -m src.analysis.eda_stage_b`. Index of average monthly weighted employment per",
             "Section 9 quarterly bin, bin -1 (Sep-Nov 2022) = 100. Main-sample months only. No age x exposure",
             "breakdown, no model, no inference.", "",
             *table(l1, i1, "## B1. By age group, quintiles pooled", "b1_employment_by_age.png"),
             *table(l2, i2, "## B2. By exposure quintile, ages pooled", "b2_employment_by_quintile.png")]
    TABLE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {TABLE.relative_to(REPO_ROOT)} and two figures")


if __name__ == "__main__":
    main()
