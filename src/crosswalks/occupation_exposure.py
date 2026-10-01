"""Phase 4, Steps 2b-3: 2010 Census occupation -> detailed SOC 2018 -> exposure; coverage report.

Chain (decisions.md, 2026-09-30):
  OCC2010 (= 2010 Census code) -> 2018 Census code -> SOC 2018 -> O*NET-SOC 2019.

2010 -> 2018 Census codes (rule set by Aryan): unchanged codes come from rows of the
"2010 to 2018 Crosswalk" sheet that carry both codes; changed codes come from the
"Occ Code Changes" sheet, whose continuation rows are forward-filled: a blank 2010 code
continues a split, a blank 2018 code continues a merge (each such row is named in the
merge note above it; tested). The main sheet's half-filled rows are a test only, because
their position does not say which code they belong to.

2018 Census -> detailed SOC 2018. Census gives one SOC code per 2018 Census code, but some
are aggregates, expanded with the BLS 2018 SOC structure:
  - detailed SOC code          -> used as is
  - major/minor/broad group    -> every detailed code under it (BLS hierarchy)
  - residual code with an X    -> every detailed code with that prefix, EXCLUDING codes
                                  claimed by any other 2018 Census code; more specific
                                  residuals claim first
Detailed codes named in parentheses in Census titles are used only as a test.

Scores: dv_rating_beta averaged (unweighted) over O*NET-SOC variants within each SOC code,
then over the scored SOC targets of each 2010 Census code.

Run from the repo root:  python -m src.crosswalks.occupation_exposure
"""
from __future__ import annotations

import re

import duckdb
import pandas as pd
from ipumspy import readers

from src.data.convert_to_parquet import locate_files
from src.data.inspect_codes import labels_for
from src.data.ipums_extract import load_log
from src.utils.config import REPO_ROOT, load_settings

MAP_FILE = REPO_ROOT / "docs" / "occ_soc_map.csv"                     # codes only, committed
REPORT_FILE = REPO_ROOT / "results" / "tables" / "exposure_coverage.md"
LEVELS = ("Major Group", "Minor Group", "Broad Group")
TITLE_SOC = re.compile(r"\(\s*(\d\d-\d{4})\s*\)")   # one title has "(17-3012 )"
CODE = r"\d{4}"


def source_path(name: str):
    s = load_settings()
    return s["paths"]["raw"] / s["design"][name]["file"], s["design"][name]


def read_main() -> pd.DataFrame:
    """The "2010 to 2018 Crosswalk" sheet as is: census2010, census2018, soc2018, title2018."""
    path, cfg = source_path("occ_crosswalk")
    df = pd.read_excel(path, sheet_name=cfg["sheet"], header=3, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"2010 Census Code": "census2010", "2018 Census Code": "census2018",
                            "2018 SOC Code": "soc2018", "2018 Census Title": "title2018"})
    df = df[["census2010", "census2018", "soc2018", "title2018"]].apply(lambda c: c.str.strip())
    for col in ("census2010", "census2018"):
        df.loc[~df[col].str.fullmatch(CODE, na=False), col] = None
    return df


def read_changes() -> pd.DataFrame:
    """The "Occ Code Changes" sheet with continuation rows forward-filled."""
    path, _ = source_path("occ_crosswalk")
    df = pd.read_excel(path, sheet_name="Occ Code Changes", header=2, dtype=str)
    df = df.iloc[:, [0, 2, 4]].apply(lambda c: c.str.strip())
    df.columns = ["census2010", "census2018", "note"]
    df = df.dropna(subset=["census2010", "census2018"], how="all")
    df["merge_continuation"] = df["census2010"].notna() & df["census2018"].isna()
    df["note"] = df["note"].ffill()
    df[["census2010", "census2018"]] = df[["census2010", "census2018"]].ffill()
    return df


def read_structure() -> tuple[set[str], dict[str, set[str]]]:
    """(detailed SOC 2018 codes, group code -> its detailed codes) from the BLS structure file.

    Membership comes from the file's own hierarchy (parents forward-filled onto each
    detailed row), not from code arithmetic: SOC numbering has exceptions such as 15-1200.
    """
    path, cfg = source_path("soc_structure")
    df = pd.read_excel(path, sheet_name=cfg["sheet"], header=7, dtype=str)
    df = df[[*LEVELS, "Detailed Occupation"]].apply(lambda c: c.str.strip())
    df[list(LEVELS)] = df[list(LEVELS)].ffill()
    df = df.dropna(subset=["Detailed Occupation"])
    members = {g: set(grp["Detailed Occupation"]) for lv in LEVELS for g, grp in df.groupby(lv)}
    return set(df["Detailed Occupation"]), members


def expand(census_soc: dict[str, str], detailed: set[str], groups: dict[str, set[str]],
           overrides: dict[str, str] | None = None) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Map each 2018 Census code to detailed SOC codes. Returns (mapping, unresolved).

    `overrides` (detailed SOC -> 2018 Census code) are claimed before residuals expand.
    """
    overrides = overrides or {}
    out: dict[str, set[str]] = {}
    unresolved: dict[str, str] = {}
    residual = {c: s for c, s in census_soc.items() if "X" in s.upper()}
    for c, s in census_soc.items():
        if c in residual:
            continue
        if s in detailed:
            out[c] = {s}
        elif s in groups:
            out[c] = set(groups[s])
        else:
            unresolved[c] = s
    claimed = set().union(*out.values()) | set(overrides)
    # Longest prefix first, so 51-403X claims before 51-4XXX.
    for c, s in sorted(residual.items(), key=lambda kv: -len(kv[1].upper().split("X")[0])):
        prefix = s.upper().split("X")[0]
        out[c] = {d for d in detailed if d.startswith(prefix)} - claimed
        claimed |= out[c]
    for soc, c in overrides.items():
        out.setdefault(c, set()).add(soc)
    unresolved |= {c: s for c, s in residual.items() if not out[c]}
    return out, unresolved


def title_codes(main: pd.DataFrame) -> dict[str, set[str]]:
    """Detailed SOC codes named in parentheses, attributed to the 2018 Census code above them."""
    named: dict[str, set[str]] = {}
    last = None
    for census2018, title in zip(main["census2018"], main["title2018"]):
        if census2018:
            last = census2018
        if last and isinstance(title, str):
            named.setdefault(last, set()).update(TITLE_SOC.findall(title))
    return {k: v for k, v in named.items() if v}


def build() -> dict:
    main, changes = read_main(), read_changes()
    pairs = pd.concat([main.dropna(subset=["census2010", "census2018"])[["census2010", "census2018"]],
                       changes[["census2010", "census2018"]]]).drop_duplicates()
    rows18 = main.dropna(subset=["census2018", "soc2018"])
    census_soc = dict(zip(rows18["census2018"], rows18["soc2018"]))
    detailed, groups = read_structure()
    overrides = load_settings()["design"]["occ_crosswalk"].get("soc_overrides", {})
    census_detail, unresolved = expand(census_soc, detailed, groups, overrides)

    all2010 = set(main["census2010"].dropna()) | set(changes["census2010"])
    rows = []
    for c10 in sorted(all2010):
        c18 = sorted(set(pairs.loc[pairs["census2010"] == c10, "census2018"]))
        socs = set().union(*(census_detail.get(c, set()) for c in c18))
        rows.append({"census2010": c10, "census2018": " ".join(c18),
                     "soc2018": " ".join(sorted(socs)), "n_soc_targets": len(socs)})
    return {"main": main, "changes": changes, "census_soc": census_soc,
            "census_detail": census_detail, "unresolved": unresolved, "detailed": detailed,
            "occ_map": pd.DataFrame(rows), "title_codes": title_codes(main)}


def soc_scores() -> pd.Series:
    """dv_rating_beta by 6-digit SOC: unweighted mean over O*NET-SOC 8-digit variants."""
    path, cfg = source_path("exposure")
    ex = pd.read_csv(path, dtype={cfg["code_column"]: str})
    return ex.groupby(ex[cfg["code_column"]].str[:7])[cfg["score_column"]].mean()


def occ_scores(occ_map: pd.DataFrame, scores: pd.Series) -> pd.DataFrame:
    """Unweighted mean over each 2010 Census code's scored SOC targets."""
    def one(socs: str) -> pd.Series:
        vals = [scores[s] for s in socs.split() if s in scores.index]
        return pd.Series({"n_soc_scored": len(vals), "exposure": sum(vals) / len(vals) if vals else None})
    out = pd.concat([occ_map[["census2010", "n_soc_targets"]], occ_map["soc2018"].apply(one)], axis=1)
    out["occ2010"] = out["census2010"].astype(int)
    return out


def cps_parquet() -> str:
    log = load_log()
    dat_path, _, _ = locate_files(log)
    return dat_path.with_name(log["parquet"]["name"]).as_posix()


def employment_by_occ() -> pd.DataFrame:
    """Weighted employment per OCC2010: employed (EMPSTAT 10, 12), wage and salary, ages 22-64.

    Columns occ2010, cutoff (True inside the Section 5 cutoff window), w (sum WTFINL), n (records).
    Pooled over months; no age breakdown.
    """
    d = load_settings()["design"]
    ws = ", ".join(str(c) for c in d["wage_salary_classwkr"])
    c0, c1 = (int(x.replace("-", "")) for x in d["quintile_cutoff_window"])
    return duckdb.connect().execute(f"""
        SELECT OCC2010 AS occ2010, (YEAR * 100 + MONTH BETWEEN {c0} AND {c1}) AS cutoff,
               SUM(WTFINL) AS w, COUNT(*) AS n
        FROM read_parquet('{cps_parquet()}')
        WHERE EMPSTAT IN (10, 12) AND CLASSWKR IN ({ws}) AND AGE BETWEEN {d['age_min']} AND {d['age_max']}
        GROUP BY 1, 2""").df()


def coverage_report(b: dict, occ: pd.DataFrame, scores: pd.Series) -> str:
    """Matched share of wage and salary employment, ages 22-64, by window. No ages, no exposure levels."""
    d = load_settings()["design"]
    parquet = cps_parquet()
    occ_labels = labels_for(readers.read_ipums_ddi(locate_files(load_log())[2]), "OCC2010")
    ws = ", ".join(str(c) for c in d["wage_salary_classwkr"])
    con = duckdb.connect()
    emp = employment_by_occ().merge(occ[["occ2010", "exposure", "n_soc_targets", "n_soc_scored"]],
                                    on="occ2010", how="left")
    emp["matched"] = emp["exposure"].notna()

    def share(df: pd.DataFrame) -> str:
        return (f"{df.loc[df.matched, 'w'].sum() / df['w'].sum():.2%} of weighted employment; "
                f"{df.loc[df.matched, 'n'].sum() / df['n'].sum():.2%} of records "
                f"({df['n'].sum():,} records, {df['occ2010'].nunique()} OCC2010 codes)")

    cut = emp[emp.cutoff]
    lines = [
        "# Exposure coverage report (Phase 4, step 3)",
        "",
        "Generated by `python -m src.crosswalks.occupation_exposure`. Population: employed",
        f"(EMPSTAT 10, 12), wage and salary (CLASSWKR {ws}), ages {d['age_min']}-{d['age_max']}.",
        "Weighted by WTFINL, pooled over months. People counts by occupation code only;",
        "nothing by age group or exposure level. No quintiles have been computed.",
        "",
        "## Matched share",
        "",
        f"- Primary, Section 5 cutoff window {d['quintile_cutoff_window'][0]} to "
        f"{d['quintile_cutoff_window'][1]}: {share(cut)}",
        f"- Check, full extract 2011-01 to 2026-08: {share(emp)}",
        "",
        "## Unmatched OCC2010 codes (cutoff window, largest first)",
        "",
        "| OCC2010 | IPUMS label | Why | Share of window employment | Present after 2019 |",
        "|---|---|---|---|---|",
    ]
    total = cut["w"].sum()
    by_occ = emp.groupby("occ2010").agg(w=("w", "sum")).join(
        cut.groupby("occ2010").agg(w_cut=("w", "sum")))
    late = set(con.execute(f"""SELECT DISTINCT OCC2010 FROM read_parquet('{parquet}')
        WHERE YEAR >= 2020 AND EMPSTAT IN (10, 12) AND CLASSWKR IN ({ws})""").df()["OCC2010"])
    um = emp[~emp.matched].drop_duplicates("occ2010").merge(by_occ, on="occ2010", how="left")
    for r in um.sort_values("w_cut", ascending=False).itertuples():
        why = ("not in Census 2010 code list" if pd.isna(r.n_soc_targets) else
               "no SOC 2018 target" if r.n_soc_targets == 0 else "no target has an Eloundou score")
        pct = f"{(r.w_cut if pd.notna(r.w_cut) else 0) / total:.3%}"
        lines.append(f"| {r.occ2010:04d} | {occ_labels.get(r.occ2010, '')} | {why} | {pct} | "
                     f"{'yes' if r.occ2010 in late else 'no'} |")

    dist = b["occ_map"]["n_soc_targets"].value_counts().sort_index()
    lines += ["", "## n_soc_targets distribution (2010 Census codes in the crosswalk)", "",
              "| SOC targets | 2010 Census codes |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in dist.items()]
    scored = occ[occ.n_soc_scored > 0]
    lines += ["", f"{(scored.n_soc_scored < scored.n_soc_targets).sum()} of {len(scored)} scored "
              "2010 Census codes have some SOC targets without an Eloundou score; their score is "
              "the mean over the scored targets only."]

    pointed = set().union(*b["census_detail"].values())
    orphan = sorted(set(scores.index) - pointed)
    lines += ["", "## SOC 2018 codes with an Eloundou score but no Census code pointing at them", "",
              f"{len(orphan)} codes: " + (", ".join(orphan) if orphan else "none"), ""]
    return "\n".join(lines)


def main() -> None:
    b = build()
    b["occ_map"].to_csv(MAP_FILE, index=False)
    print(f"Wrote {MAP_FILE.relative_to(REPO_ROOT)}: {len(b['occ_map'])} 2010 Census codes")
    print(f"Unresolved 2018 Census SOC codes: {b['unresolved']}")

    scores = soc_scores()
    occ = occ_scores(b["occ_map"], scores)
    out = load_settings()["paths"]["interim"] / "occ2010_exposure.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    occ.to_parquet(out, index=False)
    print(f"Wrote {out.relative_to(REPO_ROOT)} (scores; not committed, not printed)")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(coverage_report(b, occ, scores), encoding="utf-8")
    print(f"Wrote {REPORT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
