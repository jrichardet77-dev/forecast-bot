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
# Practice challengers (Quinn review T102, 2026-10-27): judged on clean questions, counted by event cluster, never on
# pilot batches; promotion needs 30 clusters and P(better) >= 0.975 (0.95 split across the two live challengers).
MIN_CLUSTERS, MIN_P_CHALLENGER = 30, 0.975
PILOT_BATCHES = {"20261026-221344"}  # mixed models (v1 runs not on Haiku); kept as a descriptive pilot only
# Owner decision 2026-10-28 (T102/T103): challengers are v2 and v6; v3 is exploratory only. Meeting the
# 30-cluster rule is a checkpoint; a live change also needs the same result on a fresh holdout of clean clusters.
CHALLENGERS, EXPLORATORY = ("v2", "v6"), ("v3", "v3c", "v4", "v5")


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


def clusters():
    """qid -> event cluster (data/clusters.json); a question without one is its own cluster."""
    p = ledger.DATA / "clusters.json"
    return json.loads(p.read_text()).get("clusters", {}) if p.exists() else {}


def with_v6(rows):
    """Add v6: equal-weight log-odds mean of the v1 runs each question already has (no new forecasts)."""
    runs = defaultdict(list)
    for r in ledger.read("runs"):
        if r.get("variant", "v1") == "v1":
            runs[(r["batch"], r["qid"])].append(float(r["prob"]))
    extra = []
    for r in rows:
        if r["variant"] == "v1" and runs.get((r["batch"], r["qid"])):
            p = aggregate.combine(runs[(r["batch"], r["qid"])], "mean_logodds", 1.0)
            o = r["outcome"]
            extra.append({**r, "variant": "v6", "prob": p, "brier": scoring.brier(p, o),
                          "baseline": scoring.baseline_score(p, o),
                          "vs_market": scoring.relative_score(p, float(r["market_prob"]), o)})
        if r["variant"] == "v1":  # v3c: v1's own forecast capped to 0.10-0.90 (exploratory sensitivity check)
            p, o = min(0.9, max(0.1, float(r["prob"]))), r["outcome"]
            extra.append({**r, "variant": "v3c", "prob": p, "brier": scoring.brier(p, o),
                          "baseline": scoring.baseline_score(p, o),
                          "vs_market": scoring.relative_score(p, float(r["market_prob"]), o)})
    return rows + extra


def variant_table(rows):
    """Each challenger against the champion (v1) on the same clean resolved questions, outside pilot batches.
    Paired differences are averaged within each event cluster; the bootstrap resamples clusters."""
    exposed, cl = exposed_keys(), clusters()
    clean = [r for r in rows if (r["batch"], r["qid"]) not in exposed and r["batch"] not in PILOT_BATCHES]
    champ = {(r["batch"], r["qid"]): r for r in clean if r["variant"] == "v1"}
    out = []
    for v in sorted({r["variant"] for r in clean} - {"v1"}):
        by_cluster = defaultdict(list)
        for r in clean:
            c = champ.get((r["batch"], r["qid"]))
            if r["variant"] == v and c:
                by_cluster[cl.get(r["qid"], r["qid"])].append(
                    scoring.relative_score(float(r["prob"]), float(c["prob"]), r["outcome"]))
        boot = scoring.paired_bootstrap([scoring.mean(d) for d in by_cluster.values()])
        role = "challenger" if v in CHALLENGERS else "exploratory"
        met = role == "challenger" and boot["n"] >= MIN_CLUSTERS and boot["mean"] > 0 and boot["p_better"] >= MIN_P_CHALLENGER
        out.append({"variant": v, "role": role, "n": sum(len(d) for d in by_cluster.values()), "clusters": boot["n"],
                    "vs_champion": boot["mean"], "vs_champion_lo": boot["lo"], "vs_champion_hi": boot["hi"],
                    "p_better": boot["p_better"], "accept": met,
                    "per_cluster": {k: round(scoring.mean(d), 2) for k, d in sorted(by_cluster.items())}})
    return out


def summary():
    rows = with_v6(scored_finals())
    by_variant = defaultdict(list)
    for r in rows:
        by_variant[r["variant"]].append(r)
    out = {}
    for v, rs in by_variant.items():
        if v in ("v6", "v3c"):
            continue  # derived variants are judged only against v1 on clean questions (challengers)
        boot = scoring.paired_bootstrap([r["vs_market"] for r in rs])
        out[v] = {"n": len(rs), "brier": scoring.mean(r["brier"] for r in rs),
                  "market_brier": scoring.mean(r["market_brier"] for r in rs),
                  "baseline": scoring.mean(r["baseline"] for r in rs),
                  "market_baseline": scoring.mean(r["market_baseline"] for r in rs),
                  "vs_market": boot["mean"], "vs_market_lo": boot["lo"], "vs_market_hi": boot["hi"],
                  "p_beats_market": boot["p_better"]}
    return {"variants": out, "leak_split": leak_split([r for r in rows if r["variant"] not in ("v6", "v3c")]), "challengers": variant_table(rows), "scored": rows,
            "postprocess": postprocess_table()}
