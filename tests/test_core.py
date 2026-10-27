import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fbot import aggregate, cli, evaluate, ledger, scoring, sources  # noqa: E402


class Scoring(unittest.TestCase):
    def test_baseline_score_matches_metaculus_definition(self):
        self.assertAlmostEqual(scoring.baseline_score(0.5, 1), 0)
        self.assertAlmostEqual(scoring.baseline_score(1.0, 1), 100, places=1)
        self.assertAlmostEqual(scoring.baseline_score(0.25, 1), -100)

    def test_relative_score_sign(self):
        self.assertGreater(scoring.relative_score(0.8, 0.6, 1), 0)
        self.assertLess(scoring.relative_score(0.8, 0.6, 0), 0)
        self.assertAlmostEqual(scoring.relative_score(0.7, 0.7, 1), 0)

    def test_brier(self):
        self.assertAlmostEqual(scoring.brier(0.7, 1), 0.09)
        self.assertAlmostEqual(scoring.brier(0.7, 0), 0.49)

    def test_bootstrap_detects_clear_improvement(self):
        b = scoring.paired_bootstrap([5, 6, 4, 7, 5, 6] * 6)
        self.assertGreater(b["p_better"], 0.99)
        self.assertLess(scoring.paired_bootstrap([-3, -2, -4] * 10)["p_better"], 0.01)


class Aggregate(unittest.TestCase):
    def test_median_and_logodds(self):
        self.assertAlmostEqual(aggregate.combine([0.2, 0.3, 0.9]), 0.3)
        self.assertAlmostEqual(aggregate.mean_logodds([0.5, 0.5]), 0.5)

    def test_extremize_and_clamp(self):
        self.assertGreater(aggregate.extremize(0.7, 1.5), 0.7)
        self.assertLess(aggregate.extremize(0.7, 0.5), 0.7)
        self.assertAlmostEqual(aggregate.extremize(0.5, 3), 0.5)
        self.assertEqual(aggregate.combine([0.999, 0.999, 0.999]), 0.99)


class Filters(unittest.TestCase):
    def test_sports_and_prices_excluded(self):
        for t in ["Lakers vs. Celtics", "Bitcoin above $90k on Friday?", "Will Gen.G win Worlds 2026?",
                  "Will the Milwaukee Brewers win the 2026 World Series?", "Up or Down: ETH"]:
            self.assertFalse(sources.eligible_title(t), t)
        for t in ["Will the Fed cut rates in December?", "Will Likud win 25-29 seats?"]:
            self.assertTrue(sources.eligible_title(t), t)


class Pipeline(unittest.TestCase):
    """batch -> record -> resolve -> report, on a temporary data folder with no network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.saved = (ledger.DATA, cli.PACKETS, cli.BATCHES)
        ledger.DATA, cli.PACKETS, cli.BATCHES = root / "data", root / "packets", root / "data" / "batches"
        ledger.DATA.mkdir()
        pool = [{"qid": f"pm:{i}", "source": "polymarket", "title": f"Question number {i} about topic {i}",
                 "description": "d", "close_time": "2026-11-01T00:00:00+00:00", "url": "u",
                 "market_prob": 0.5, "activity": 1, "fetched_at": "x"} for i in range(40)]
        (ledger.DATA / "pool.json").write_text(json.dumps(pool))

    def tearDown(self):
        ledger.DATA, cli.PACKETS, cli.BATCHES = self.saved
        self.tmp.cleanup()

    def test_full_cycle_and_market_price_hidden(self):
        batch = cli.cmd_batch(["--n", "35", "--seed", "3"])
        packet = json.loads((cli.PACKETS / batch / "questions.json").read_text())
        self.assertEqual(len(packet), 35)
        self.assertNotIn("market_prob", packet[0])
        runs = cli.PACKETS / batch / "runs"
        for who, p in (("A", 0.8), ("B", 0.7), ("C", 0.9)):
            (runs / f"{who}.json").write_text(json.dumps([{"qid": q["qid"], "prob": p} for q in packet]))
        cli.cmd_record([batch])
        finals = ledger.read("final")
        self.assertEqual(len(finals), 35)
        self.assertAlmostEqual(float(finals[0]["prob"]), 0.8)
        ledger.append("resolutions", [{"qid": f["qid"], "outcome": 1, "resolved_at": "t"} for f in finals])
        s = evaluate.summary()
        v = s["variants"]["v1"]
        self.assertEqual(v["n"], 35)
        self.assertAlmostEqual(v["vs_market"], 100 * math.log(0.8 / 0.5), places=6)
        self.assertGreater(v["p_beats_market"], 0.99)
        accepted = {r["variant"] for r in s["postprocess"] if r["accept"]}
        self.assertIn("median_x1.3", accepted)  # all outcomes YES, so extremizing a correct lean must win

    def test_batch_skips_already_forecast(self):
        b1 = cli.cmd_batch(["--n", "5", "--seed", "1"])
        packet = json.loads((cli.PACKETS / b1 / "questions.json").read_text())
        (cli.PACKETS / b1 / "runs" / "A.json").write_text(json.dumps([{"qid": q["qid"], "prob": 0.6} for q in packet]))
        cli.cmd_record([b1])
        b2_qids = {q["qid"] for q in json.loads((cli.BATCHES / f"{b1}.json").read_text())}
        import time
        time.sleep(1.1)  # batch ids are per second
        b2 = cli.cmd_batch(["--n", "5", "--seed", "1"])
        self.assertFalse(b2_qids & {q["qid"] for q in json.loads((cli.BATCHES / f"{b2}.json").read_text())})

    def test_variants_leaks_and_short_horizon(self):
        import datetime as dt
        pool = json.loads((ledger.DATA / "pool.json").read_text())
        soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=10)).isoformat()
        later = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=90)).isoformat()
        for i, q in enumerate(pool):
            q["close_time"] = soon if i < 34 else later
        (ledger.DATA / "pool.json").write_text(json.dumps(pool))
        batch = cli.cmd_batch(["--n", "40", "--seed", "2", "--max-days", "21"])
        packet = json.loads((cli.PACKETS / batch / "questions.json").read_text())
        self.assertEqual(len(packet), 34)  # the questions closing in 90 days are left out
        runs = cli.PACKETS / batch / "runs"
        leak = packet[0]["qid"]
        for who, p in (("A", 0.7), ("B", 0.7), ("C", 0.7)):
            (runs / f"{who}.json").write_text(json.dumps(
                [{"qid": q["qid"], "prob": p, "saw_market_price": q["qid"] == leak and who == "B"} for q in packet]))
        (runs / "v2").mkdir()
        (runs / "v2" / "A.json").write_text(json.dumps([{"qid": q["qid"], "prob": 0.9} for q in packet]))
        (runs / "v5").mkdir()
        for who in ("D", "E"):
            (runs / "v5" / f"{who}.json").write_text(json.dumps([{"qid": q["qid"], "prob": 0.95} for q in packet]))
        cli.cmd_record([batch])
        cli.cmd_record([batch, "--variant", "v2"])
        cli.cmd_record([batch, "--variant", "v5", "--with", "v1"])
        self.assertEqual(json.loads((ledger.DATA / "exposed.json").read_text())[batch], [leak])
        finals = ledger.read("final")
        v5 = [f for f in finals if f["variant"] == "v5"]
        self.assertEqual({f["n_runs"] for f in v5}, {"5"})
        self.assertAlmostEqual(float(v5[0]["prob"]), 0.7)  # median of 0.7, 0.7, 0.7, 0.95, 0.95
        ledger.append("resolutions", [{"qid": q["qid"], "outcome": 1, "resolved_at": "t"} for q in packet])
        s = evaluate.summary()
        self.assertEqual((s["leak_split"]["v1 clean"]["n"], s["leak_split"]["v1 leaked"]["n"]), (33, 1))
        ch = {c["variant"]: c for c in s["challengers"]}
        self.assertEqual(ch["v2"]["n"], 33)  # judged on clean questions only
        self.assertTrue(ch["v2"]["accept"])  # 0.9 beats 0.7 on 33 YES outcomes
        self.assertFalse(ch["v5"]["accept"])  # same median as v1, so no gain
        self.assertEqual(ch["v2"]["clusters"], 33)  # no clusters file: each question is its own cluster
        clean_qids = [q["qid"] for q in packet if q["qid"] != leak]
        (ledger.DATA / "clusters.json").write_text(json.dumps({"clusters": {q: "same-event" for q in clean_qids[:10]}}))
        ch = {c["variant"]: c for c in evaluate.summary()["challengers"]}
        self.assertEqual((ch["v2"]["n"], ch["v2"]["clusters"]), (33, 24))  # 10 related questions count once
        self.assertFalse(ch["v2"]["accept"])  # 24 clusters is below the 30-cluster minimum
        saved = set(evaluate.PILOT_BATCHES)
        evaluate.PILOT_BATCHES.add(batch)
        try:
            self.assertEqual(evaluate.summary()["challengers"], [])  # pilot batches never count
        finally:
            evaluate.PILOT_BATCHES.clear()
            evaluate.PILOT_BATCHES.update(saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
