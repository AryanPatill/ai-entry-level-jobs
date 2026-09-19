"""Load project settings and secrets."""
from functools import lru_cache
from pathlib import Path
import os

import yaml
from dotenv import load_dotenv

# src/utils/config.py -> parents[2] is the repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = REPO_ROOT / "config" / "settings.yaml"


@lru_cache(maxsize=1)
def load_settings() -> dict:
    """Read settings.yaml and convert every entry under `paths` to an absolute Path."""
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    settings["paths"] = {k: REPO_ROOT / v for k, v in settings["paths"].items()}
    return settings


def get_secret(name: str) -> str:
    """Return a secret from .env or the environment; fail loudly if it is missing."""
    load_dotenv(REPO_ROOT / ".env")
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill it in."
        )
    return value