"""Phase 4, Step 1: download the Eloundou et al. exposure file and verify its SHA-256.

URL, expected hash and destination come from config/settings.yaml (design.exposure).
The file is written to a temporary name and kept only if the hash matches, so a wrong
or partial download never sits where later stages would read it.

Run from the repo root:  python -m src.data.download_exposure
"""
from __future__ import annotations

import urllib.request

from src.data.ipums_extract import file_sha256
from src.utils.config import load_settings


def main() -> None:
    settings = load_settings()
    exp = settings["design"]["exposure"]
    dest = settings["paths"]["raw"] / exp["file"]

    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        urllib.request.urlretrieve(exp["url"], tmp)
        got = file_sha256(tmp)
        if got != exp["sha256"]:
            tmp.unlink()
            raise RuntimeError(f"SHA-256 mismatch for {exp['url']}\n  expected {exp['sha256']}\n  got      {got}")
        tmp.replace(dest)
        print(f"Downloaded {dest}")

    got = file_sha256(dest)
    if got != exp["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for existing {dest}\n  expected {exp['sha256']}\n  got      {got}")
    print(f"SHA-256 OK: {got}")


if __name__ == "__main__":
    main()
