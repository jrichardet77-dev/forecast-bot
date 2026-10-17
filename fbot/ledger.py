"""Append-only records in data/. Every forecast is kept with the market price at the moment it was made,
so later scoring is fair and nothing is rewritten after the outcome is known."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FILES = {
    "runs": ("runs.csv", ["batch", "made_at", "qid", "runner", "variant", "prob"]),
    "final": ("final.csv", ["batch", "made_at", "qid", "variant", "prob", "market_prob", "n_runs"]),
    "resolutions": ("resolutions.csv", ["qid", "outcome", "resolved_at", "note"]),
    "official": ("official.csv", ["submitted_at", "qid", "prob", "note"]),
}


def path(name):
    return DATA / FILES[name][0]


def read(name):
    p = path(name)
    if not p.exists():
        return []
    with p.open(newline="") as f:
        return list(csv.DictReader(f))


def append(name, rows):
    p = path(name)
    DATA.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FILES[name][1])
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FILES[name][1]})


def questions():
    p = DATA / "questions.jsonl"
    out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            q = json.loads(line)
            out[q["qid"]] = q
    return out


def add_questions(qs):
    known = questions()
    with (DATA / "questions.jsonl").open("a") as f:
        for q in qs:
            if q["qid"] not in known:
                f.write(json.dumps(q) + "\n")
