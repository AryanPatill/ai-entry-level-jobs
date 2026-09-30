"""Phase 4: download the non-IPUMS source files and verify each SHA-256.

Sources (URL, expected hash, destination) come from config/settings.yaml:
design.exposure (Eloundou et al.), design.occ_crosswalk (Census 2018 occupation list) and
design.soc_structure (BLS 2018 SOC structure). Each file is written to a temporary name and
kept only if the hash matches, so a wrong or partial download never sits where later stages
would read it. The hash is re-checked on every run.

Sources marked `manual: true` are never downloaded: BLS blocks automated requests, so that
file is saved by hand and only verified here.

Run from the repo root:  python -m src.data.download_sources
"""
from __future__ import annotations

import urllib.request

from src.data.ipums_extract import file_sha256
from src.utils.config import load_settings

SOURCES = ("exposure", "occ_crosswalk", "soc_structure")


def fetch(src: dict, raw_dir) -> None:
    dest = raw_dir / src["file"]
    if not dest.exists() and src.get("manual"):
        raise RuntimeError(
            f"{dest} is missing. This source blocks automated download: open\n  {src['url']}\n"
            f"in a browser and save the file to that path, then re-run."
        )
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        urllib.request.urlretrieve(src["url"], tmp)
        got = file_sha256(tmp)
        if got != src["sha256"]:
            tmp.unlink()
            raise RuntimeError(f"SHA-256 mismatch for {src['url']}\n  expected {src['sha256']}\n  got      {got}")
        tmp.replace(dest)
        print(f"Downloaded {dest}")

    got = file_sha256(dest)
    if got != src["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch for existing {dest}\n  expected {src['sha256']}\n  got      {got}")
    print(f"SHA-256 OK  {dest.name}  {got}")


def main() -> None:
    settings = load_settings()
    for name in SOURCES:
        fetch(settings["design"][name], settings["paths"]["raw"])


if __name__ == "__main__":
    main()
