"""Phase 3, Step 3: convert the downloaded fixed-width extract to Parquet, then run structural checks.

Reads the .dat.gz with its DDI codebook (.xml) in chunks, so memory stays low.
The checks are structural only: rows, months, ages, columns, weights. There are no
employment or occupation tabulations here; outcomes stay unseen until the analysis
panel is built (preregistration Section 16).

Run from the repo root:
    python -m src.data.convert_to_parquet            convert (if needed), then check
    python -m src.data.convert_to_parquet --force    rebuild the Parquet file, then check
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from ipumspy import readers

from src.data.extract_definition import month_range
from src.data.ipums_extract import file_sha256, load_log, save_log
from src.utils.config import REPO_ROOT

DEFINITION_FILE = REPO_ROOT / "docs" / "extract_definition.json"
CHUNK_ROWS = 500_000


def locate_files(log: dict) -> tuple[Path, str, Path]:
    """Return (data file, its logged sha256, codebook file) from the extract log."""
    folder = REPO_ROOT / log["download_dir"]
    by_suffix = {Path(f["name"]).suffix: f for f in log["files"]}   # ".gz" and ".xml"
    return folder / by_suffix[".gz"]["name"], by_suffix[".gz"]["sha256"], folder / by_suffix[".xml"]["name"]


def convert(dat_path: Path, xml_path: Path, out_path: Path) -> int:
    """Stream the fixed-width file into one Parquet file. Returns the row count."""
    ddi = readers.read_ipums_ddi(xml_path)
    tmp_path = out_path.with_name(out_path.name + ".tmp")   # a failed run never leaves a half file
    writer, n_rows, t0 = None, 0, time.time()
    try:
        for chunk in readers.read_microdata_chunked(ddi, dat_path, chunksize=CHUNK_ROWS):
            # Every chunk must match the first chunk's schema; a mismatch raises instead of drifting.
            schema = writer.schema if writer else None
            table = pa.Table.from_pandas(chunk, schema=schema, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(tmp_path, table.schema, compression="zstd")
            writer.write_table(table)
            n_rows += len(chunk)
            print(f"  {n_rows:>12,} rows   {time.time() - t0:6.0f} s")
    finally:
        if writer is not None:
            writer.close()
    tmp_path.replace(out_path)
    return n_rows


def check(out_path: Path, record: dict) -> None:
    """Structural checks on the Parquet file. Prints a report; changes nothing."""
    con = duckdb.connect()
    src = f"read_parquet('{out_path.as_posix()}')"

    columns = [row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()]
    requested = list(record["variable_reasons"])
    absent = [v for v in requested if v not in columns]

    n_rows = con.execute(f"SELECT COUNT(*) FROM {src}").fetchone()[0]
    per_month = {
        f"{y:04d}-{m:02d}": n
        for y, m, n in con.execute(
            f"SELECT YEAR, MONTH, COUNT(*) FROM {src} GROUP BY 1, 2 ORDER BY 1, 2"
        ).fetchall()
    }
    expected = [m for m in month_range(record["first_month"], record["last_month"])
                if m not in record["missing_months"]]
    months_absent = [m for m in expected if m not in per_month]
    months_extra = [m for m in per_month if m not in expected]
    smallest = min(per_month, key=per_month.get)
    largest = max(per_month, key=per_month.get)

    age_min, age_max = con.execute(f"SELECT MIN(AGE), MAX(AGE) FROM {src}").fetchone()
    wt_null, wt_nonpos = con.execute(
        f"SELECT COUNT(*) FILTER (WHERE WTFINL IS NULL), "
        f"COUNT(*) FILTER (WHERE WTFINL <= 0) FROM {src}"
    ).fetchone()
    null_counts = con.execute(
        "SELECT " + ", ".join(f'COUNT(*) - COUNT("{c}")' for c in requested if c in columns)
        + f" FROM {src}"
    ).fetchone()

    print("\n=== Structural checks ===")
    print(f"Rows:                  {n_rows:,}")
    print(f"Columns ({len(columns)}):          {', '.join(columns)}")
    print(f"Requested but absent:  {absent if absent else 'none'}")
    print(f"Months with data:      {len(per_month)} (expected {len(expected)})")
    print(f"Expected, not found:   {months_absent if months_absent else 'none'}")
    print(f"Found, not expected:   {months_extra if months_extra else 'none'}")
    print(f"Rows per month:        min {per_month[smallest]:,} ({smallest}), "
          f"max {per_month[largest]:,} ({largest})")
    print(f"AGE range:             {age_min} to {age_max} (expected 22 to 64)")
    print(f"WTFINL null / <= 0:    {wt_null:,} / {wt_nonpos:,}")
    print("Nulls per requested column:")
    for name, nulls in zip([c for c in requested if c in columns], null_counts):
        print(f"  {name:10s} {nulls:>12,}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the IPUMS extract to Parquet and check it.")
    parser.add_argument("--force", action="store_true", help="rebuild the Parquet file")
    args = parser.parse_args()

    log = load_log()
    record = json.loads(DEFINITION_FILE.read_text(encoding="utf-8"))
    dat_path, logged_sha, xml_path = locate_files(log)
    out_path = dat_path.with_name(dat_path.name.replace(".dat.gz", ".parquet"))

    if out_path.exists() and not args.force:
        print(f"Parquet file exists, skipping conversion: {out_path.relative_to(REPO_ROOT).as_posix()}")
    else:
        print("Verifying the download against the logged hash ...")
        if file_sha256(dat_path) != logged_sha:
            raise SystemExit(f"{dat_path.name} does not match its logged SHA-256. Re-download it.")
        print(f"Converting {dat_path.name} in chunks of {CHUNK_ROWS:,} rows ...")
        n_rows = convert(dat_path, xml_path, out_path)
        log["parquet"] = {"name": out_path.name, "rows": n_rows}
        save_log(log)
        size_mb = out_path.stat().st_size / 1e6
        print(f"Wrote {out_path.relative_to(REPO_ROOT).as_posix()}  ({n_rows:,} rows, {size_mb:.1f} MB)")

    check(out_path, record)


if __name__ == "__main__":
    main()