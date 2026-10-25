"""forecast-bot command line: python3 -m fbot.cli <command>

  pool                      fetch open questions (Polymarket, Manifold) into data/pool.json
  batch --n N [--seed S]    pick N new, diverse questions; write packets/<batch>/questions.json for forecasters
                            (market prices are kept out of the packet and stored in data/batches/<batch>.json)
  record BATCH [--variant V] read packets/<batch>/runs/*.json, store every run and the combined forecast
  resolve                   look up outcomes for every forecast question that has not resolved yet
  report                    score everything; write DASHBOARD.md, docs/dashboard.html and data/report.json
  official-scores           read-only: look up resolutions and AlmanacBot's scores for its official forecasts
                            (needs METACULUS_TOKEN; runs daily in GitHub Actions) into data/official_scores.csv
"""
import datetime as dt
import json
import random
import re
import sys
from pathlib import Path

from . import aggregate, dashboard, evaluate, ledger, official, sources

ROOT = ledger.ROOT
PACKETS = ROOT / "packets"
BATCHES = ledger.DATA / "batches"


def _arg(args, name, default=None, cast=str):
    return cast(args[args.index(name) + 1]) if name in args else default


def cmd_pool():
    qs = []
    for fetch in (sources.polymarket_open, sources.manifold_open):
        try:
            qs += fetch()
        except Exception as e:  # one source down should not stop the other
            print(f"WARNING: {fetch.__name__}: {e}")
    (ledger.DATA / "pool.json").write_text(json.dumps(qs, indent=1))
    print(f"pool: {len(qs)} questions")


def _key(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(w for w in words if w not in {"will", "the", "a", "in", "of", "by", "be", "win", "party"})[:40]


def cmd_batch(args):
    n, seed = _arg(args, "--n", 12, int), _arg(args, "--seed", None, int)
    pool = json.loads((ledger.DATA / "pool.json").read_text())
    done = {f["qid"] for f in ledger.read("final")}
    rng = random.Random(seed)
    rng.shuffle(pool)
    picked, seen = [], set()
    for q in pool:
        k = _key(q["title"])[:24]
        if q["qid"] in done or k in seen:
            continue
        seen.add(k)
        picked.append(q)
        if len(picked) == n:
            break
    for q in picked:
        if q["source"] == "manifold" and not q["description"]:
            try:
                q["description"] = sources.manifold_details(q["qid"].split(":", 1)[1])[:4000]
            except Exception:
                pass
    batch = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    (PACKETS / batch / "runs").mkdir(parents=True, exist_ok=True)
    blind = [{k: q[k] for k in ("qid", "title", "description", "close_time", "url")} for q in picked]
    (PACKETS / batch / "questions.json").write_text(json.dumps(blind, indent=1))
    BATCHES.mkdir(parents=True, exist_ok=True)
    (BATCHES / f"{batch}.json").write_text(json.dumps(picked, indent=1))
    ledger.add_questions(picked)
    print(f"batch {batch}: {len(picked)} questions -> packets/{batch}/questions.json")
    return batch


def cmd_record(args):
    batch, variant = args[0], _arg(args, "--variant", "v1")
    meta = {q["qid"]: q for q in json.loads((BATCHES / f"{batch}.json").read_text())}
    runs = {}
    for f in sorted((PACKETS / batch / "runs").glob("*.json")):
        for r in json.loads(f.read_text()):
            p = float(r["prob"])
            if r["qid"] in meta and 0 <= p <= 1:
                runs.setdefault(r["qid"], []).append((f.stem, p))
    made = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    ledger.append("runs", [{"batch": batch, "made_at": made, "qid": q, "runner": who, "variant": variant, "prob": p}
                           for q, rs in runs.items() for who, p in rs])
    champ = evaluate.CHAMPION
    finals = [{"batch": batch, "made_at": made, "qid": q, "variant": variant, "n_runs": len(rs),
               "prob": round(aggregate.combine([p for _, p in rs], champ["method"], champ["a"]), 4),
               "market_prob": meta[q]["market_prob"]} for q, rs in runs.items()]
    ledger.append("final", finals)
    print(f"recorded {sum(len(r) for r in runs.values())} runs, {len(finals)} forecasts for batch {batch}")


def cmd_resolve():
    have = {r["qid"] for r in ledger.read("resolutions")}
    todo = sorted({f["qid"] for f in ledger.read("final")} - have)
    new = []
    for q in todo:
        try:
            r = sources.resolution(q)
        except Exception as e:
            print(f"WARNING {q}: {e}")
            continue
        if r:
            new.append(r)
    ledger.append("resolutions", new)
    print(f"resolved {len(new)} of {len(todo)} open")


def cmd_report():
    s = evaluate.summary()
    dashboard.write(s)
    print(json.dumps(s["variants"], indent=1))


def cmd_official_scores():
    checked, resolved = official.update()
    print(f"checked {checked} official questions; {resolved} resolved in total")
    print(official.summary_text(official.summary()))


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    {"pool": lambda: cmd_pool(), "batch": lambda: cmd_batch(args), "record": lambda: cmd_record(args),
     "resolve": lambda: cmd_resolve(), "report": lambda: cmd_report(),
     "official-scores": lambda: cmd_official_scores()}[cmd]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
