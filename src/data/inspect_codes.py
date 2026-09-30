"""Phase 3, Step 3b: check coded values that null counts cannot see.

IPUMS never leaves a cell empty. People outside a variable's universe get an
NIU ("not in universe") code instead, so zero nulls says nothing about coverage.
This script reads codes with their labels from the DDI codebook.
People counts only; no employment or occupation trends (preregistration Section 16).

Run from the repo root:  python -m src.data.inspect_codes
"""
from __future__ import annotations

import duckdb
from ipumspy import readers

from src.data.convert_to_parquet import locate_files
from src.data.ipums_extract import load_log
from src.utils.config import load_settings


def labels_for(ddi, name: str) -> dict[int, str]:
    """Code -> label, from the codebook (ipumspy stores label -> code)."""
    return {int(code): label for label, code in ddi.get_variable_info(name).codes.items()}


def main() -> None:
    log = load_log()
    dat_path, _, xml_path = locate_files(log)
    parquet = dat_path.with_name(log["parquet"]["name"])
    ddi = readers.read_ipums_ddi(xml_path)
    con = duckdb.connect()
    src = f"read_parquet('{parquet.as_posix()}')"

    # 1. Who has a zero or negative final weight?
    n_zero, n_neg = con.execute(
        f"SELECT COUNT(*) FILTER (WHERE WTFINL = 0), COUNT(*) FILTER (WHERE WTFINL < 0) FROM {src}"
    ).fetchone()
    print(f"WTFINL = 0: {n_zero:,}     WTFINL < 0: {n_neg:,}")
    emp = labels_for(ddi, "EMPSTAT")
    print("EMPSTAT among records with WTFINL <= 0:")
    for code, n in con.execute(
        f"SELECT EMPSTAT, COUNT(*) FROM {src} WHERE WTFINL <= 0 GROUP BY 1 ORDER BY 1"
    ).fetchall():
        print(f"  {code:>3}  {emp.get(int(code), '(no label)'):40s} {n:>10,}")

    # 2. Does SCHLCOLL cover age 25? (preregistration Section 4 condition)
    sch = labels_for(ddi, "SCHLCOLL")
    print("\nSCHLCOLL by age, all months pooled:")
    for age, code, n in con.execute(
        f"SELECT AGE, SCHLCOLL, COUNT(*) FROM {src} WHERE AGE BETWEEN 22 AND 26 "
        f"GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall():
        print(f"  age {age}  {code:>2}  {sch.get(int(code), '(no label)'):40s} {n:>10,}")

    # 3. How has the monthly sample size changed?
    print("\nAverage records per month, by year:")
    for year, avg, months in con.execute(
        f"SELECT YEAR, COUNT(*) / COUNT(DISTINCT MONTH), COUNT(DISTINCT MONTH) "
        f"FROM {src} GROUP BY 1 ORDER BY 1"
    ).fetchall():
        print(f"  {year}  {avg:>10,.0f}   ({months} months)")

    # 4. When does SCHLCOLL cover each age? NIU share by year, civilians only.
    print("\nSCHLCOLL NIU share by year, civilians only (EMPSTAT != 1):")
    print("  year     age 22    age 23    age 24    age 25")
    shares: dict[int, dict[int, float]] = {}
    for year, age, share in con.execute(
        f"SELECT YEAR, AGE, AVG(CASE WHEN SCHLCOLL = 0 THEN 1.0 ELSE 0.0 END) "
        f"FROM {src} WHERE AGE BETWEEN 22 AND 25 AND EMPSTAT <> 1 "
        f"GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall():
        shares.setdefault(year, {})[age] = share
    for year in sorted(shares):
        cells = "   ".join(f"{shares[year].get(age, float('nan')):7.1%}" for age in range(22, 26))
        print(f"  {year}   {cells}")

    # 5. Universes: the DDI has no <universe> element, so show which EMPSTAT codes get
    #    an NIU code in each job variable. Shares within EMPSTAT only, all months pooled.
    print("\nNIU share within each EMPSTAT code (OCC and IND use 0 as NIU):")
    niu = {"LABFORCE": 0, "CLASSWKR": 0, "OCC2010": 9999, "OCC": 0,
           "IND1990": 0, "IND": 0, "UHRSWORK1": 999}
    cols = ", ".join(f"AVG(CASE WHEN {v} = {c} THEN 1.0 ELSE 0.0 END)" for v, c in niu.items())
    print("  EMPSTAT  " + "".join(f"{v:>10}" for v in niu))
    for code, *s in con.execute(f"SELECT EMPSTAT, {cols} FROM {src} GROUP BY 1 ORDER BY 1").fetchall():
        print(f"  {code:>3} {emp.get(int(code), '')[:4]:4s} " + "".join(f"{x:>10.1%}" for x in s))

    # 6. CLASSWKR codes by year, before the wage-and-salary filter is applied. Any code used
    #    in some years but not in settings.design.wage_salary_classwkr would be dropped
    #    silently, especially the aggregate codes (20, 21, 24).
    cw = labels_for(ddi, "CLASSWKR")
    keep = set(load_settings()["design"]["wage_salary_classwkr"])
    counts: dict[int, dict[int, int]] = {}
    for year, code, n in con.execute(
        f"SELECT YEAR, CLASSWKR, COUNT(*) FROM {src} GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall():
        counts.setdefault(int(code), {})[year] = n
    years = sorted({y for by_year in counts.values() for y in by_year})
    print(f"\nCLASSWKR records by year (* = in wage_salary_classwkr {sorted(keep)}):")
    print("  code  label" + " " * 29 + "".join(f"{y:>9}" for y in years))
    for code in sorted(counts):
        mark = "*" if code in keep else " "
        cells = "".join(f"{counts[code].get(y, 0):>9,}" for y in years)
        print(f" {mark}{code:>3}  {cw.get(code, '(no label)')[:34]:34s}{cells}")
    absent = sorted(set(cw) - set(counts))
    print("  labelled in DDI, never used: " + ", ".join(f"{c} {cw[c]}" for c in absent))


if __name__ == "__main__":
    main()