"""Scores for AlmanacBot's official Metaculus forecasts (data/official.csv) once their questions resolve.

Read-only: one GET per question to /api/posts/{id}/ with the bot's own token. Nothing is submitted, edited or
previewed, and the forecasting bot is not run. Already-resolved questions are not fetched again.

Metaculus returns the bot's own scores in question.my_forecasts.score_data (keys "<score_type>_score", for example
peer_score and baseline_score); those are recorded as score_source "metaculus". If a resolved question has no
score_data, a baseline score is computed locally from our last published forecast for binary and multiple-choice
questions (score_source "computed locally"; not time-averaged like Metaculus's own score). Numeric and discrete
questions are not computed locally.
"""
import csv
import json
import math
import re
import time

from . import ledger, sources

OFFICIAL = ledger.DATA / "official.csv"
SCORES = ledger.DATA / "official_scores.csv"
FIELDS = ["post_id", "title", "type", "status", "resolved_at", "resolution", "our_forecast", "peer_score",
          "baseline_score", "score_source", "checked_at"]
UNSCORED = {"annulled", "ambiguous"}


def post_id(url):
    m = re.search(r"/questions/(\d+)", url)
    return m.group(1) if m else None


def latest_forecasts(path=None):
    """Last published forecast per post id: {post_id: {"type": ..., "prediction": ...}}."""
    out, path = {}, path or OFFICIAL
    if not path.exists():
        return out
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            pid = post_id(r["question_url"])
            if pid and r.get("published") == "True":
                out[pid] = {"type": r["type"], "prediction": r["prediction"]}
    return out


def parse_binary(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_options(text):
    """{option name: probability} from the logged predicted_options text (may be cut short in the log)."""
    return {m.group(1): float(m.group(2)) for m in
            re.finditer(r"option_name='((?:[^'\\]|\\.)*)', probability=([0-9.eE-]+)", text or "")}


def local_baseline(qtype, prediction, resolution):
    """Metaculus baseline score, 100 * ln(N * p) / ln(N), from our forecast; None when it cannot be computed."""
    if resolution is None or str(resolution).lower() in UNSCORED:
        return None
    if qtype == "BinaryQuestion":
        p = parse_binary(prediction)
        if p is None or str(resolution).lower() not in ("yes", "no"):
            return None
        p = p if str(resolution).lower() == "yes" else 1 - p
        n = 2
    elif qtype == "MultipleChoiceQuestion":
        opts = parse_options(prediction)
        if str(resolution) not in opts:
            return None
        p, n = opts[str(resolution)], len(opts)
        if n < 2:
            return None
    else:
        return None
    p = min(1 - 1e-4, max(1e-4, p))
    return round(100 * math.log(n * p) / math.log(n), 1)


def summarize_forecast(qtype, prediction):
    if qtype == "BinaryQuestion":
        p = parse_binary(prediction)
        return "" if p is None else f"{p:.0%}"
    if qtype == "MultipleChoiceQuestion":
        return "; ".join(f"{k} {v:.0%}" for k, v in parse_options(prediction).items())
    return "distribution (see official.csv)"


def score_row(pid, post, ours):
    """One output row from a /api/posts/{id}/ response and our logged forecast."""
    q = post.get("question") or {}
    resolution = q.get("resolution")
    status = q.get("status") or post.get("status") or ""
    resolved = status == "resolved" or (resolution not in (None, "") and q.get("actual_resolve_time"))
    sd = ((q.get("my_forecasts") or {}).get("score_data") or {}) if resolved else {}
    peer, base, source = sd.get("peer_score"), sd.get("baseline_score"), ""
    if peer is not None or base is not None:
        source = "metaculus"
    elif resolved:
        base = local_baseline(ours.get("type"), ours.get("prediction"), resolution)
        source = "computed locally" if base is not None else "not computed"
    return {"post_id": pid, "title": q.get("title") or post.get("title", ""), "type": ours.get("type", ""),
            "status": "resolved" if resolved else (status or "open"),
            "resolved_at": (q.get("actual_resolve_time") or "")[:10] if resolved else "",
            "resolution": "" if resolution is None else str(resolution),
            "our_forecast": summarize_forecast(ours.get("type"), ours.get("prediction")),
            "peer_score": "" if peer is None else round(float(peer), 1),
            "baseline_score": "" if base is None else round(float(base), 1), "score_source": source,
            "checked_at": sources.now_iso()}


def read_scores(path=None):
    path = path or SCORES
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        return {r["post_id"]: r for r in csv.DictReader(f)}


def write_scores(rows, path=None):
    with (path or SCORES).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in sorted(rows.values(), key=lambda r: int(r["post_id"])):
            w.writerow({k: r.get(k, "") for k in FIELDS})


def update(fetch=None, pause=1.0, official_path=None, scores_path=None):
    """Check every forecast question that has not resolved yet; returns (checked, resolved_total)."""
    official_path, scores_path = official_path or OFFICIAL, scores_path or SCORES
    if fetch is None:
        headers = {"Authorization": f"Token {sources.metaculus_token()}"}
        fetch = lambda pid: sources._get(f"{sources.METACULUS}/posts/{pid}/", headers)  # noqa: E731
    ours, rows = latest_forecasts(official_path), read_scores(scores_path)
    checked = 0
    for pid in sorted(ours, key=int):
        if rows.get(pid, {}).get("status") == "resolved":
            continue
        try:
            rows[pid] = score_row(pid, fetch(pid), ours[pid])
            checked += 1
        except Exception as e:  # one unreadable question never stops the rest
            print(f"WARNING post {pid}: {type(e).__name__}: {e}")
        time.sleep(pause)
    write_scores(rows, scores_path)
    return checked, sum(r["status"] == "resolved" for r in rows.values())


def summary(rows=None):
    rows = list((rows if rows is not None else read_scores()).values())
    res = [r for r in rows if r["status"] == "resolved"]

    def avg(key):
        xs = [float(r[key]) for r in res if r.get(key) not in ("", None)]
        return (round(sum(xs) / len(xs), 1), len(xs)) if xs else (None, 0)

    peer, n_peer = avg("peer_score")
    base, n_base = avg("baseline_score")
    return {"tracked": len(rows), "resolved": len(res), "avg_peer_score": peer, "n_peer": n_peer,
            "avg_baseline_score": base, "n_baseline": n_base,
            "local_scores": sum(r.get("score_source") == "computed locally" for r in res)}


def dashboard_rows(rows=None):
    rows = rows if rows is not None else read_scores()
    return [{"post_id": r["post_id"], "question": r["title"], "type": r["type"], "resolved": r["resolved_at"],
             "resolution": r["resolution"], "our_forecast": r["our_forecast"],
             "peer_score": None if r["peer_score"] == "" else float(r["peer_score"]),
             "baseline_score": None if r["baseline_score"] == "" else float(r["baseline_score"]),
             "score_source": r["score_source"], "url": f"https://www.metaculus.com/questions/{r['post_id']}/"}
            for r in rows.values() if r["status"] == "resolved"]


def summary_text(s):
    if not s["resolved"]:
        return "No official questions resolved yet."
    parts = [f"{s['resolved']} of {s['tracked']} official questions resolved"]
    if s["avg_peer_score"] is not None:
        parts.append(f"average peer score {s['avg_peer_score']:+.1f} ({s['n_peer']} scored)")
    if s["avg_baseline_score"] is not None:
        parts.append(f"average baseline score {s['avg_baseline_score']:+.1f} ({s['n_baseline']} scored"
                     + (f", {s['local_scores']} computed locally" if s["local_scores"] else "") + ")")
    return "; ".join(parts) + "."


if __name__ == "__main__":
    print(json.dumps(summary(), indent=1))
