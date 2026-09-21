"""Phase 3, Step 4a: list every IND1990 code in the extract, with its codebook label.

Preregistration Section 15 requires the broad industry sectors to be mapped from the
IPUMS industry codebook in Phase 3, before any outcome analysis. This lists the codes
so the mapping is written from real labels, not from memory.
Counts are pooled people counts (civilians, all months, all ages together); no trends.

Run from the repo root:  python -m src.data.list_industry_codes
"""
from __future__ import annotations

import csv

import duckdb
from ipumspy import readers

from src.data.convert_to_parquet import locate_files
from src.data.inspect_codes import labels_for
from src.data.ipums_extract import load_log
from src.utils.config import REPO_ROOT

OUT_FILE = REPO_ROOT / "docs" / "ind1990_codes.csv"


def main() -> None:
    log = load_log()
    dat_path, _, xml_path = locate_files(log)
    parquet = dat_path.with_name(log["parquet"]["name"])
    labels = labels_for(readers.read_ipums_ddi(xml_path), "IND1990")

    con = duckdb.connect()
    rows = con.execute(
        f"SELECT IND1990, COUNT(*), BOOL_OR(YEAR < 2020), BOOL_OR(YEAR >= 2020) "
        f"FROM read_parquet('{parquet.as_posix()}') "
        f"WHERE EMPSTAT <> 1 "            # civilians only
        f"GROUP BY 1 ORDER BY 1"
    ).fetchall()

    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ind1990", "label", "n_people", "in_2011_2019", "in_2020_2026"])
        for code, n, pre, post in rows:
            writer.writerow([int(code), labels.get(int(code), "(no label)"), n, pre, post])

    unlabeled = [int(c) for c, *_ in rows if int(c) not in labels]
    only_pre = [int(c) for c, _, pre, post in rows if pre and not post]
    only_post = [int(c) for c, _, pre, post in rows if post and not pre]
    print(f"IND1990 codes in the extract: {len(rows)}  (codebook lists {len(labels)})")
    print(f"Codes with no codebook label: {unlabeled if unlabeled else 'none'}")
    print(f"Codes only in 2011-2019:      {only_pre if only_pre else 'none'}")
    print(f"Codes only in 2020-2026:      {only_post if only_post else 'none'}")
    print(f"Written to:                   {OUT_FILE.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()