"""Phase 3, Step 2: submit the committed extract definition, check status, download.

Submits docs/extract_definition.json exactly as committed, so the data always
matches what is in git. Extract metadata (number, dates, file hashes) goes to
docs/extract_log.json; the microdata goes to data/raw/ and is never committed.

Usage, from the repo root:
    python -m src.data.ipums_extract submit
    python -m src.data.ipums_extract status
    python -m src.data.ipums_extract download
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ipumspy import IpumsApiClient

from src.utils.config import REPO_ROOT, get_secret, load_settings

DEFINITION_FILE = REPO_ROOT / "docs" / "extract_definition.json"
LOG_FILE = REPO_ROOT / "docs" / "extract_log.json"
COLLECTION = "cps"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def definition_sha256(definition: dict) -> str:
    """Fingerprint of the definition, independent of key order and whitespace."""
    return hashlib.sha256(json.dumps(definition, sort_keys=True).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_log() -> dict:
    return json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else {}


def save_log(log: dict) -> None:
    LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")


def require_number(log: dict) -> int:
    if "extract_number" not in log:
        raise SystemExit("No extract submitted yet. Run: python -m src.data.ipums_extract submit")
    return int(log["extract_number"])


def cmd_submit(client: IpumsApiClient, force: bool) -> None:
    log = load_log()
    if "extract_number" in log and not force:
        raise SystemExit(
            f"Extract {log['extract_number']} was already submitted at {log['submitted_utc']} UTC.\n"
            "Use `status` or `download`. Pass --force only if you mean to submit a new one."
        )
    record = json.loads(DEFINITION_FILE.read_text(encoding="utf-8"))
    definition = record["extract"]

    extract = client.submit_extract(definition)   # IPUMS validates samples and variables here

    save_log({
        "extract_number": extract.extract_id,
        "collection": COLLECTION,
        "submitted_utc": now_utc(),
        "definition_built_utc": record["built_utc"],
        "definition_sha256": definition_sha256(definition),
        "first_month": record["first_month"],
        "last_month": record["last_month"],
        "n_samples": record["n_samples"],
    })
    print(f"Submitted: extract {extract.extract_id} ({record['n_samples']} samples, "
          f"{record['first_month']} to {record['last_month']})")
    print(f"Logged to:  {LOG_FILE.relative_to(REPO_ROOT)}")
    print("Next: python -m src.data.ipums_extract status")


def cmd_status(client: IpumsApiClient) -> None:
    number = require_number(load_log())
    print(f"Extract {number}: {client.extract_status(number, collection=COLLECTION)}")


def cmd_download(client: IpumsApiClient) -> None:
    log = load_log()
    number = require_number(log)
    status = client.extract_status(number, collection=COLLECTION)
    if status != "completed":
        raise SystemExit(f"Extract {number} is '{status}', not 'completed'. Try again later.")

    out_dir = load_settings()["paths"]["raw"] / f"cps_extract_{number:05d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    client.download_extract(number, collection=COLLECTION, download_dir=out_dir)

    files = sorted(p for p in out_dir.iterdir() if p.is_file())
    log["downloaded_utc"] = now_utc()
    log["download_dir"] = out_dir.relative_to(REPO_ROOT).as_posix()
    log["files"] = [
        {"name": p.name, "bytes": p.stat().st_size, "sha256": file_sha256(p)} for p in files
    ]
    save_log(log)

    for p in files:
        print(f"{p.name:40s} {p.stat().st_size / 1e6:10.1f} MB")
    print(f"Saved to:   {log['download_dir']}")
    print(f"Logged to:  {LOG_FILE.relative_to(REPO_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit, check, and download the IPUMS CPS extract.")
    parser.add_argument("command", choices=["submit", "status", "download"])
    parser.add_argument("--force", action="store_true", help="submit even if one is already logged")
    args = parser.parse_args()

    client = IpumsApiClient(get_secret("IPUMS_API_KEY"))
    if args.command == "submit":
        cmd_submit(client, args.force)
    elif args.command == "status":
        cmd_status(client)
    else:
        cmd_download(client)


if __name__ == "__main__":
    main()