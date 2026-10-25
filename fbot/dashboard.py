"""Dashboard data: data/report.json, DASHBOARD.md (readable in the GitHub iPhone app) and three row files in
data/dashboard/ that the phone dashboard page loads (forecasts, scores, progress, official_scores)."""
import json

from . import evaluate, ledger, official, scoring

OUT = ledger.DATA / "dashboard"

# Project milestones; status is one of: done, owner, next, later.
PROGRESS = [
    ("Research the competition rules and what wins", "done", "docs/RESEARCH.md"),
    ("Practice harness: blind questions, scoring vs market", "done", "Daily check at 8:52 ET"),
    ("First practice batch (12 questions, 3 runs each)", "done", "Batch 20261017-1423; first results from Oct 25"),
    ("Second practice batch (12 questions, 3 runs each)", "done", "Batch 20261018-125311; 24 practice questions open"),
    ("GitHub repository forecast-bot", "done", "Created by you; project uploaded Oct 17"),
    ("Metaculus account and AlmanacBot", "done", "Bot key stored as a GitHub secret"),
    ("AI models via OpenRouter ($25 prepaid, no top-up)", "done", "Luna x2, DeepSeek x2, Sonnet x1; Sonar research"),
    ("Test run on the unscored test area", "done", "9 of 9 questions forecast, nothing submitted"),
    ("Official forecasting switched on", "done", "Every 30 minutes since Oct 17; 84 official forecasts published, all runs green (Oct 25)"),
    ("Participation form", "done", "Submitted by you Oct 17"),
    ("Official-forecast scoring", "done", "Daily read-only lookup of resolutions and AlmanacBot's scores (Oct 25)"),
    ("Apply for free credits for Spring 2027", "later", "Applications reopen a few weeks before January"),
]


def _exposed():
    p = ledger.DATA / "exposed.json"
    return {q for qs in (json.loads(p.read_text()).values() if p.exists() else []) for q in qs}


def rows_forecasts():
    qs, exposed = ledger.questions(), _exposed()
    outcomes = evaluate.resolved_outcomes()
    rows = []
    for f in ledger.read("final"):
        q = qs.get(f["qid"], {})
        p, m = float(f["prob"]), float(f["market_prob"])
        o = outcomes.get(f["qid"])
        rows.append({"qid": f["qid"], "question": q.get("title", f["qid"]), "source": q.get("source", ""),
                     "closes": (q.get("close_time") or "")[:10], "bot": p, "market": m, "runs": int(f["n_runs"]),
                     "status": "open" if o is None else ("YES" if o else "NO"),
                     "vs_market": None if o is None else round(scoring.relative_score(p, m, o), 1),
                     "exposed": f["qid"] in exposed, "url": q.get("url", ""), "made": f["made_at"][:10]})
    return rows


def rows_scores(summary):
    out = []
    for name, v in summary["variants"].items():
        out.append({"method": name, "resolved": v["n"], "vs_market": round(v["vs_market"], 1),
                    "vs_market_lo": round(v["vs_market_lo"], 1), "vs_market_hi": round(v["vs_market_hi"], 1),
                    "p_beats_market": round(v["p_beats_market"], 2), "brier": round(v["brier"], 3),
                    "market_brier": round(v["market_brier"], 3)})
    if not out:
        out.append({"method": "v1", "resolved": 0, "vs_market": None, "vs_market_lo": None, "vs_market_hi": None,
                    "p_beats_market": None, "brier": None, "market_brier": None})
    return out


def write(summary):
    (ledger.DATA / "report.json").write_text(json.dumps(summary, indent=1, default=str))
    OUT.mkdir(exist_ok=True)
    fc, sc = rows_forecasts(), rows_scores(summary)
    (OUT / "forecasts.json").write_text(json.dumps(fc, indent=1))
    (OUT / "scores.json").write_text(json.dumps(sc, indent=1))
    (OUT / "progress.json").write_text(json.dumps([{"step": s, "status": st, "note": n} for s, st, n in PROGRESS],
                                                  indent=1))
    (OUT / "official_scores.json").write_text(json.dumps(official.dashboard_rows(), indent=1))
    lines = ["# Forecast bot dashboard", "", "Official tournament forecasts: " + official.summary_text(official.summary()),
             "", "Practice forecasts: " + f"{len(fc)}; resolved: {sum(r['status'] != 'open' for r in fc)}",
             "", "| Question | Bot | Market | Status | vs market |", "|---|---|---|---|---|"]
    for r in fc:
        vm = "" if r["vs_market"] is None else f"{r['vs_market']:+.1f}"
        lines.append(f"| {r['question'][:70]} | {r['bot']:.0%} | {r['market']:.0%} | {r['status']} | {vm} |")
    (ledger.ROOT / "DASHBOARD.md").write_text("\n".join(lines) + "\n")
