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


if __name__ == "__main__":
    main()