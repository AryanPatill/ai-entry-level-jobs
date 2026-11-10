"""Local LLM access (Phase 11): Ollama via langchain-ollama, settings from config/settings.yaml (agents)."""
from __future__ import annotations

import json
import os
import urllib.request

from src.utils.config import load_settings

os.environ["LANGSMITH_TRACING"] = "false"   # never send prompts or outputs to LangSmith


def cfg() -> dict:
    return load_settings()["agents"]


def available(model: str | None = None) -> bool:
    """True if the Ollama server answers and has the model pulled."""
    try:
        with urllib.request.urlopen(cfg()["host"] + "/api/tags", timeout=3) as r:
            names = {m["name"] for m in json.load(r)["models"]}
    except OSError:
        return False
    return (model or cfg()["model"]) in names


def chat(model: str | None = None):
    from langchain_ollama import ChatOllama
    c = cfg()
    return ChatOllama(model=model or c["model"], base_url=c["host"], temperature=c["temperature"])
