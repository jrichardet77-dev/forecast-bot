"""Score resolved forecasts and compare variants.

Primary metric: relative log score vs the market price at the moment of forecasting (Metaculus peer-score style,
100 * ln(p_bot / p_market) on the outcome). Positive means we beat the market on that question.

Acceptance rule for changes (EXPERIMENTS.md): a challenger replaces the champion only when, on the same resolved
questions, its mean relative score vs the champion is positive with bootstrap P(better) >= 0.90 and n >= 30.
"""
import json
from collections import defaultdict

from . import aggregate, ledger, scoring

CHAMPION = {"name": "median", "method": "median", "a": 1.0}
POSTPROCESS_GRID = [
    {"name": "median", "method": "median", "a": 1.0},
    {"name": "mean_logodds", "method": "mean_logodds", "a": 1.0},
    {"name": "median_x1.3", "method": "median", "a": 1.3},
    {"name": "median_x0.8", "method": "median", "a": 0.8},
    {"name": "mean_logodds_x1.3", "method": "mean_logodds", "a": 1.3},
]
MIN_N, MIN_P = 30, 0.90


def resolved_outcomes():
    return {r["qid"]: int(r["outcome"]) for r in ledger.read("resolutions") if r["outcome"] in ("0", "1")}


def scored_finals():
    outcomes = resolved_outcomes()
    rows = []
    for f in ledger.read("final"):
        if f["qid"] in outcomes:
            p, m, o = float(f["prob"]), float(f["market_prob"]), outcomes[f["qid"]]
            rows.append({**f, "outcome": o, "brier": scoring.brier(p, o), "market_brier": scoring.brier(m, o),
                         "baseline": scoring.baseline_score(p, o), "market_baseline": scoring.baseline_score(m, o),
                         "vs_market": scoring.relative_score(p, m, o)})
    return rows


def postprocess_table():
    """Re-aggregate the recorded raw runs under each post-processing rule; compare with the champion."""
    outcomes = resolved_outcomes()
    market = {(f["batch"], f["qid"]): float(f["market_prob"]) for f in ledger.read("final")}
    runs = defaultdict(list)
    for r in ledger.read("runs"):
        if r.get("variant", "v1") == "v1":  # post-processing rules re-aggregate the champion's own runs
            runs[(r["batch"], r["qid"])].append(float(r["prob"]))
    keys = [k for k in runs if k[1] in outcomes and k in market]
    table = []
    champ = {k: aggregate.combine(runs[k], CHAMPION["method"], CHAMPION["a"]) for k in keys}
    for v in POSTPROCESS_GRID:
        probs = {k: aggregate.combine(runs[k], v["method"], v["a"]) for k in keys}
        vs_m = [scoring.relative_score(probs[k], market[k], outcomes[k[1]]) for k in keys]
        vs_c = [scoring.relative_score(probs[k], champ[k], outcomes[k[1]]) for k in keys]
        boot = scoring.paired_bootstrap(vs_c)
        table.append({"variant": v["name"], "n": len(keys), "vs_market": scoring.mean(vs_m),
                      "brier": scoring.mean(scoring.brier(probs[k], outcomes[k[1]]) for k in keys),
                      "vs_champion": boot["mean"], "p_better": boot["p_better"],
                      "accept": v["name"] != CHAMPION["name"] and boot["n"] >= MIN_N and boot["mean"] > 0
                      and boot["p_better"] >= MIN_P})
    return table


def exposed_keys():
    """(batch, qid) pairs where a forecaster saw a market price; those results are scored separately."""
    p = ledger.DATA / "exposed.json"
    data = json.loads(p.read_text()) if p.exists() else {}
    return {(b, q) for b, qs in data.items() for q in qs}


def _stats(rs):
    boot = scoring.paired_bootstrap([r["vs_market"] for r in rs])
    return {"n": len(rs), "brier": scoring.mean(r["brier"] for r in rs),
            "market_brier": scoring.mean(r["market_brier"] for r in rs),
            "baseline": scoring.mean(r["baseline"] for r in rs),
            "market_baseline": scoring.mean(r["market_baseline"] for r in rs),
            "vs_market": boot["mean"], "vs_market_lo": boot["lo"], "vs_market_hi": boot["hi"],
            "p_beats_market": boot["p_better"]}


def leak_split(rows):
    """Champion results split into clean (no market price seen) and leaked."""
    exposed = exposed_keys()
    v1 = [r for r in rows if r["variant"] == "v1"]
    clean = [r for r in v1 if (r["batch"], r["qid"]) not in exposed]
    leaked = [r for r in v1 if (r["batch"], r["qid"]) in exposed]
    return {"v1 clean": _stats(clean), "v1 leaked": _stats(leaked)}


def variant_table(rows):
    """Each challenger against the champion (v1) on the same clean resolved questions; acceptance rule applied."""
    exposed = exposed_keys()
    clean = [r for r in rows if (r["batch"], r["qid"]) not in exposed]
    champ = {(r["batch"], r["qid"]): r for r in clean if r["variant"] == "v1"}
    out = []
    for v in sorted({r["variant"] for r in clean} - {"v1"}):
        pairs = [(r, champ[(r["batch"], r["qid"])]) for r in clean
                 if r["variant"] == v and (r["batch"], r["qid"]) in champ]
        diffs = [scoring.relative_score(float(r["prob"]), float(c["prob"]), r["outcome"]) for r, c in pairs]
        boot = scoring.paired_bootstrap(diffs)
        out.append({"variant": v, "n": boot["n"], "vs_champion": boot["mean"], "p_better": boot["p_better"],
                    "accept": boot["n"] >= MIN_N and boot["mean"] > 0 and boot["p_better"] >= MIN_P})
    return out


def summary():
    rows = scored_finals()
    by_variant = defaultdict(list)
    for r in rows:
        by_variant[r["variant"]].append(r)
    out = {}
    for v, rs in by_variant.items():
        boot = scoring.paired_bootstrap([r["vs_market"] for r in rs])
        out[v] = {"n": len(rs), "brier": scoring.mean(r["brier"] for r in rs),
                  "market_brier": scoring.mean(r["market_brier"] for r in rs),
                  "baseline": scoring.mean(r["baseline"] for r in rs),
                  "market_baseline": scoring.mean(r["market_baseline"] for r in rs),
                  "vs_market": boot["mean"], "vs_market_lo": boot["lo"], "vs_market_hi": boot["hi"],
                  "p_beats_market": boot["p_better"]}
    return {"variants": out, "leak_split": leak_split(rows), "challengers": variant_table(rows), "scored": rows,
            "postprocess": postprocess_table()}
