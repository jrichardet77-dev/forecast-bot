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


if __name__ == "__main__":
    unittest.main(verbosity=2)
