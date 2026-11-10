"""The registry: every number the analysis reported, flattened to dotted keys (Phase 11).

Built from results/registry/*.json, which the analysis modules write. Agents cite keys from here;
they never compute or invent a number.
"""
from __future__ import annotations

import json
from functools import lru_cache

from src.utils.config import REPO_ROOT

REGISTRY_DIR = REPO_ROOT / "results" / "registry"


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


@lru_cache(maxsize=1)
def load() -> dict:
    out = {}
    for f in sorted(REGISTRY_DIR.glob("*.json")):
        out.update(flatten(json.loads(f.read_text(encoding="utf-8")), f.stem + "."))
    return out


def numbers() -> list[float]:
    return [float(v) for v in load().values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
