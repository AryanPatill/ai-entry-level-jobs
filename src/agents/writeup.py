"""Phase 11.6: every sentence of the results write-up goes through the claim pipeline.

Each entry is one sentence of the results section: an id, what it must say, and the registry prefixes the
Writer may cite. The LLM Writer drafts, code renders registry numbers, the Skeptic and the grounded reviewer
check, and the revise loop runs up to max_revisions. Accepted sentences -> results/writeup/claims.json;
every draft and every rule that fired -> results/tables/phase11_writeup_claims.md.

Run from the repo root:  python -m src.agents.writeup [--only CLAIM_ID] [--model NAME] [--no-cache]
Accepted claims are cached on (claim id, topic, the registry values it may cite, model, rule-set hash), so a re-run
reprocesses only claims whose inputs, model or rules changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time

from src.agents.llm import available, cfg
from src.agents.pipeline import llm_reviewer, run
from src.agents.writer import keys_for, llm_writer
from src.utils.config import REPO_ROOT

TABLE = REPO_ROOT / "results" / "tables" / "phase11_writeup_claims.md"
OUT = REPO_ROOT / "results" / "writeup" / "claims.json"
CACHE = REPO_ROOT / "results" / "writeup" / "cache.json"         # git-ignored; --no-cache ignores it
TRACES = REPO_ROOT / "results" / "tables" / "phase11_traces"
RULE_FILES = ("skeptic.py", "writer.py", "pipeline.py")   # the rule set: rules, render check, feedback, review
H, L3, R = "phase8_main.", "phase8_main.l3_within_age_q5_vs_q1.", "phase9_robustness.checks."
# Claim ids allowed to carry no registry number (rule number_required, Aryan 2026-11-11). Closed list.
NUMBER_FREE = frozenset({"limitations", "method", "verdict_language"})

CLAIMS = [
    ("headline", "The headline estimate for 22-25-year-olds in Q5 occupations, its 95% CI and verdict, what it is relative to, "
                 "and the within-ages-22-25 Q5-vs-Q1 change.", (H + "headline.", L3 + "22-25.")),
    ("comparison_group", "How the two within-age comparisons differ: Q5 vs Q1 within ages 22-25 and within ages 35-49.", (L3,)),
    ("pretrend", "The preregistered pre-trend test for the Q5 x 22-25 event study and whether it flagged a pre-trend.", (H + "pretrend.",)),
    ("timing", "How the Q5 x 22-25 event-study estimate compares in the first post-treatment bin and the latest bin.",
     (H + "event_study_q5_a22.2022-12.", H + "event_study_q5_a22.2026-06.")),
    ("gradient", "The estimates for ages 22-25 in quintiles Q2, Q3 and Q4, relative to Q1 and ages 35-49.",
     (H + "terms.q2_a22.", H + "terms.q3_a22.", H + "terms.q4_a22.")),
    ("step", "The Q5 estimate for ages 26-34, relative to Q1 and ages 35-49.", (H + "terms.q5_a26.",)),
    ("unemployment", "The unemployment-rate result for Q5 x 22-25, in percentage points, with its Holm-adjusted p-value.",
     (H + "secondary_q5_a22.Unemployment rate (points).",)),
    ("hours", "The mean-usual-hours result for Q5 x 22-25, in hours, with its Holm-adjusted p-value.",
     (H + "secondary_q5_a22.Mean usual weekly hours.",)),
    ("randomization", "The randomization-inference p-value for the headline and how many shuffles were run.",
     ("phase9_randomization_inference.",)),
    ("placebo_dates", "The two placebo-date estimates (December 2017 and December 2018).", (R + "T7 placebo date",)),
    ("placebo_group", "The placebo-group estimate (ages 50-64 vs 35-49), which the preregistration treats as a warning sign "
                      "if clearly non-zero.", (R + "Placebo group",)),
    ("tech_finance", "How the headline changes when tech and finance are dropped and with industry x age x month fixed effects.",
     (R + "T1(a)", R + "T1(b)")),
    ("period", "How the headline changes when the sample starts in 2011 and when it ends in December 2024.",
     (R + "Start in 2011-01", R + "L2(b)")),
    ("controls", "How the headline changes with the pre-treatment growth control and the teleworkability control.",
     (R + "T2 ", R + "T3 ")),
    ("subgroups", "The subgroup estimates for men, women and bachelor's-or-higher, with Holm-adjusted p-values and verdicts.",
     ("phase10_heterogeneity.subgroups.",)),
    ("sectors", "The exploratory sector estimates for finance and for information and professional services.",
     ("phase10_heterogeneity.sectors_exploratory.Finance", "phase10_heterogeneity.sectors_exploratory.Information")),
]


def rules_hash() -> str:
    src = REPO_ROOT / "src" / "agents"
    return hashlib.sha256(b"".join((src / f).read_bytes() for f in RULE_FILES)).hexdigest()[:16]


def cache_key(cid: str, topic: str, keys: dict, model: str) -> str:
    blob = json.dumps([cid, topic, sorted(keys.items()), model, cfg().get("seed"), rules_hash()], ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def trace(cid: str, topic: str, model: str, out: dict) -> str:
    """Every draft in order, every rule that fired, and the exact text that triggered it."""
    lines = [f"# Trace: {cid}", "", f"Model `{model}`, seed {cfg().get('seed')}; rule set {rules_hash()}; status **{out['status']}** after "
             f"{out['attempts']} draft(s). Agent output, not analysis.", "", f"Topic: {topic}", ""]
    for h in out["history"]:
        lines += [f"## Draft {h['attempt']}", "", "Template (model output):", "", f"> {h['template']}", "",
                  "Rendered claim:", "", f"> {h['claim'] or '(not rendered: template rejected)'}", ""]
        if not h["issues"]:
            lines += ["Rules fired: none (passed).", ""]
        for i in h["issues"]:
            q = f' Triggered by: "{i["quote"]}".' if i["quote"] else " Triggered by: absence (nothing to quote)."
            lines.append(f"- **{i['rule']}**: {i['detail']}.{q}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run one claim id end to end")
    ap.add_argument("--model", help="Ollama model (default: settings agents.model)")
    ap.add_argument("--no-cache", action="store_true", help="reprocess every claim")
    a = ap.parse_args()
    model = a.model or cfg()["model"]
    assert available(model), f"{model} is not available on {cfg()['host']}"
    claims = [c for c in CLAIMS if not a.only or c[0] == a.only]
    assert claims, f"unknown claim id {a.only!r}; ids: {[c[0] for c in CLAIMS]}"
    writer, reviewer = llm_writer(model), llm_reviewer(model)
    cache = {} if a.no_cache or not CACHE.exists() else json.loads(CACHE.read_text(encoding="utf-8"))
    TRACES.mkdir(parents=True, exist_ok=True)
    results = []
    for cid, topic, prefixes in claims:
        keys = keys_for(*prefixes)
        assert keys, f"{cid}: no registry keys for {prefixes}"
        k = cache_key(cid, topic, keys, model)
        if k in cache:
            results.append(cache[k])
            print(f"{cid}: cached ({cache[k]['status']})", flush=True)
            continue
        t = time.time()
        out = run(topic, keys, writer, reviewer, cfg()["max_revisions"], require_number=cid not in NUMBER_FREE)
        claim = out.get("claim")
        r = {"id": cid, "status": out["status"], "attempts": out["attempts"], "model": model, "seed": cfg().get("seed"),
             "rules": rules_hash(),
             "label": claim.label if claim else None, "text": claim.text if claim else None,
             "refs": list(claim.refs) if claim else [],
             "rules_fired": [i["rule"] for h in out["history"] for i in h["issues"]], "seconds": round(time.time() - t)}
        results.append(r)
        (TRACES / f"{cid}.md").write_text(trace(cid, topic, model, out), encoding="utf-8")
        if out["status"] == "accepted":   # only accepted claims are cached; rejections are always re-run
            cache[k] = r
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{cid}: {out['status']} after {out['attempts']} draft(s) on {model}; trace results/tables/phase11_traces/{cid}.md", flush=True)

    if a.only:   # a single-claim run does not rewrite the write-up
        return
    accepted = [r for r in results if r["status"] == "accepted"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps([{k: r.get(k) for k in ("id", "label", "text", "refs", "model", "seed", "rules")} for r in accepted],
                              indent=1, ensure_ascii=False), encoding="utf-8")
    first = sum(r["attempts"] == 1 for r in accepted)
    lines = ["# Phase 11.6: write-up claims through the pipeline (agent output, not analysis)", "",
             f"Generated by `python -m src.agents.writeup`. Max revisions {cfg()['max_revisions']}; rule set {rules_hash()}. "
             "Every number was filled in by code from results/registry. Per-claim traces: results/tables/phase11_traces/.", "",
             f"- Claims: {len(results)}; accepted {len(accepted)}; rejected {len(results) - len(accepted)}.",
             f"- Passed on the first draft: {first}; needed revisions: {len(accepted) - first}; "
             f"most revisions for an accepted claim: {max((r['attempts'] - 1 for r in accepted), default=0)}.", "",
             "| Claim | Status | Drafts | Model | Label | Rules fired (all drafts) |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['status']} | {r['attempts']} | {r['model']} | {r['label']} | {', '.join(r['rules_fired']) or '—'} |"
              for r in results]
    TABLE.write_text("\n".join(lines + [""]), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
