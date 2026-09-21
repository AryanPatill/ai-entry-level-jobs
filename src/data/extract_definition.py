"""Phase 3, Step 1: turn the preregistered design into an IPUMS CPS extract definition.

This module DEFINES the extract and saves it to docs/. It does not submit anything.
Submission and download happen in Step 2.

Run from the repo root:  python -m src.data.extract_definition
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from ipumspy import IpumsApiClient, MicrodataExtract

from src.utils.config import REPO_ROOT, get_secret, load_settings

# Every variable we request, with the preregistration section that requires it.
# IPUMS also auto-includes YEAR, SERIAL, MONTH, CPSID, CPSIDP, PERNUM, ASECFLAG.
VARIABLES: dict[str, str] = {
    "WTFINL":    "S.6  basic monthly person weight; the primary outcome is its sum",
    "AGE":       "S.4  age groups; also the case-selection variable",
    "SEX":       "S.14 subgroups (men, women)",
    "EDUC":      "S.4/S.14 bachelor's-or-higher subgroup and robustness sample",
    "EMPSTAT":   "S.6  employed / unemployed / not in labor force",
    "LABFORCE":  "S.6  cross-check on the EMPSTAT recode",
    "CLASSWKR":  "S.4  wage and salary employees; S.13 private-sector-only robustness",
    "OCC2010":   "S.5  primary occupation code (harmonized)",
    "OCC":       "S.12 threat 6: contemporary codes, to test the Jan 2020 code change",
    "IND1990":   "S.12 threat 1 and S.15 sectors (harmonized industry)",
    "IND":       "S.15 sector mapping cross-check against the contemporary codebook",
    "UHRSWORK1": "S.6  usual weekly hours at main job; S.13 full-time filter",
    "SCHLCOLL":  "S.4  student filter [verify: basic-monthly universe may end at age 24]",
}

SAMPLE_ID_RE = re.compile(r"^cps(\d{4})_(\d{2})([a-z])$")


def month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def month_range(first: str, last: str) -> list[str]:
    """Every calendar month from first to last inclusive, as 'YYYY-MM'."""
    y0, m0 = (int(x) for x in first.split("-"))
    y1, m1 = (int(x) for x in last.split("-"))
    out, y, m = [], y0, m0
    while (y, m) <= (y1, m1):
        out.append(month_key(y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
DESC_RE = re.compile(r"^IPUMS-CPS, (" + "|".join(MONTH_NAMES) + r") (\d{4})$")


def find_basic_monthly(all_samples: dict[str, str], start: str) -> dict[str, str]:
    """Map 'YYYY-MM' -> sample id for every basic monthly CPS sample from `start` on.

    A sample counts as basic monthly only if its description is exactly
    "IPUMS-CPS, <Month> <Year>" (ASEC descriptions read "IPUMS-CPS, ASEC <Year>").
    IDs use both 's' and 'b' suffixes for basic monthly files, so the suffix is ignored.
    """
    found: dict[str, str] = {}
    for sample_id, description in all_samples.items():
        id_match = SAMPLE_ID_RE.match(sample_id)
        desc_match = DESC_RE.match(description)
        if not id_match or not desc_match:
            continue
        year, month = int(id_match.group(1)), int(id_match.group(2))
        desc_month = MONTH_NAMES.index(desc_match.group(1)) + 1
        desc_year = int(desc_match.group(2))
        if (year, month) != (desc_year, desc_month):
            raise ValueError(f"ID and description disagree: {sample_id} vs '{description}'")
        key = month_key(year, month)
        if key < start:
            continue
        if key in found:
            raise ValueError(f"Two basic monthly samples for {key}: {found[key]}, {sample_id}")
        found[key] = sample_id
    return dict(sorted(found.items()))


def build_extract(sample_ids: list[str], age_min: int, age_max: int, description: str):
    extract = MicrodataExtract(
        collection="cps",
        samples=sample_ids,
        variables=list(VARIABLES),
        description=description,
        data_format="fixed_width",       # keeps IPUMS value labels via the DDI codebook
        data_structure={"rectangular": {"on": "P"}},   # one row per person
    )
    # Person-level case selection. IPUMS defaults caseSelectWho to "individuals",
    # so only the matching people are returned, not their whole households.
    extract.select_cases("AGE", list(range(age_min, age_max + 1)))
    return extract


def main() -> None:
    settings = load_settings()
    design = settings["design"]
    prereg_version = settings["project"]["preregistration_version"]
    start = design["download_start"]
    age_min, age_max = design["age_min"], design["age_max"]

    client = IpumsApiClient(get_secret("IPUMS_API_KEY"))
    samples_by_month = find_basic_monthly(client.get_all_sample_info("cps"), start)
    if not samples_by_month:
        raise RuntimeError(f"No basic monthly CPS samples found from {start} onward.")

    months = list(samples_by_month)
    first, last = months[0], months[-1]
    missing = [m for m in month_range(first, last) if m not in samples_by_month]

    description = (
        f"AI exposure and young-worker employment; prereg v{prereg_version}; "
        f"CPS basic monthly {first} to {last}; ages {age_min}-{age_max}"
    )
    extract = build_extract(list(samples_by_month.values()), age_min, age_max, description)
    extract.api_version = client.api_version   # else "version": null is saved and IPUMS rejects it
    definition = extract.build()

    out_path = REPO_ROOT / "docs" / "extract_definition.json"
    record = {
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "preregistration_version": prereg_version,
        "first_month": first,
        "last_month": last,
        "n_samples": len(months),
        "missing_months": missing,
        "variable_reasons": VARIABLES,
        "extract": definition,
    }
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print(f"Basic monthly samples found: {len(months)}  ({first} to {last})")
    print(f"Months with no sample:       {missing if missing else 'none'}")
    print(f"Variables requested:         {len(VARIABLES)}  {', '.join(VARIABLES)}")
    print(f"Case selection:              AGE {age_min}-{age_max}")
    print(f"Format / structure:          {definition['dataFormat']} / rectangular on person")
    print(f"Definition written to:       {out_path.relative_to(REPO_ROOT)}")
    print("\nNothing was submitted. Step 2 submits this definition.")


if __name__ == "__main__":
    main()