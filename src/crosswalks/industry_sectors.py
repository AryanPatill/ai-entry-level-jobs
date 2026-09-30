"""Phase 3, Step 4b: map IND1990 industry codes to the six preregistered sectors.

Preregistration Section 15 defines six broad sectors; this module fixes the code
mapping before any outcome analysis. Sectors 1 and 2 together also define
"tech and finance" for the threat-1 test (Section 12).

Rule A (chosen 2026-09-21): where the 1990 Census grouping and NAICS disagree,
follow NAICS. Mixed codes that cannot be split (e.g. 172) stay in their 1990 group.

Run from the repo root:  python -m src.crosswalks.industry_sectors
"""
from __future__ import annotations

import csv

from src.utils.config import REPO_ROOT

CODES_FILE = REPO_ROOT / "docs" / "ind1990_codes.csv"
MAP_FILE = REPO_ROOT / "docs" / "industry_sector_map.csv"

SECTOR_NAMES = {
    1: "Information and professional/technical services",
    2: "Finance, insurance, and real estate",
    3: "Manufacturing",
    4: "Wholesale and retail trade",
    5: "Education, health, and social services",
    6: "All other",
}

# Sector 1 is assembled from codes spread across the 1990 scheme.
SECTOR_1_CODES = frozenset({
    12,             # Veterinary services (NAICS 5419; Rule A)
    171,            # Newspaper publishing and printing (NAICS 511; Rule A)
    440, 441, 442,  # Broadcasting, wired and other communications
    721,            # Advertising
    732,            # Computer and data processing services
    800,            # Theaters and motion pictures (NAICS 512; Rule A)
    841,            # Legal services
    852,            # Libraries (NAICS 519; Rule A)
    882,            # Engineering, architectural, and surveying services
    890,            # Accounting, auditing, and bookkeeping
    891,            # Research, development, and testing
    892,            # Management and public relations
})
EATING_AND_DRINKING = 641   # NAICS 722 food services, not retail (Rule A): goes to sector 6

TECH_AND_FINANCE_SECTORS = frozenset({1, 2})   # threat-1 test, Section 12


def sector_for(code: int) -> int | None:
    """Sector 1-6 for an IND1990 code; None for 0 (NIU, no industry)."""
    if code == 0:
        return None
    if code in SECTOR_1_CODES:
        return 1
    if 700 <= code <= 712:
        return 2
    if 100 <= code <= 392:
        return 3
    if 500 <= code <= 691 and code != EATING_AND_DRINKING:
        return 4
    if 812 <= code <= 871:
        return 5
    return 6


def main() -> None:
    with open(CODES_FILE, newline="", encoding="utf-8") as f:
        codes = list(csv.DictReader(f))

    totals = {s: 0 for s in SECTOR_NAMES}
    n_codes = {s: 0 for s in SECTOR_NAMES}
    with open(MAP_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ind1990", "label", "sector", "sector_name", "n_people"])
        for row in codes:
            code, n = int(row["ind1990"]), int(row["n_people"])
            sector = sector_for(code)
            writer.writerow([code, row["label"], sector if sector else "",
                             SECTOR_NAMES[sector] if sector else "No industry (NIU)", n])
            if sector:
                totals[sector] += n
                n_codes[sector] += 1

    coded = sum(totals.values())
    print(f"IND1990 codes mapped: {len(codes)}  (code 0 = NIU gets no sector)")
    print("Civilians per sector, all months and ages pooled:")
    for s, name in SECTOR_NAMES.items():
        print(f"  {s}  {name:50s} {n_codes[s]:>4} codes  {totals[s]:>10,}  {totals[s] / coded:6.1%}")
    print(f"Written to: {MAP_FILE.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()