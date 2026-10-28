"""Practice rules from Quinn's review and the owner's 2026-10-28 decision: no double counting, exposure log,
question eligibility, v6 aggregation, exploratory v3, valid report.json."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fbot import aggregate, cli, dashboard, evaluate, ledger  # noqa: E402


class PracticeRules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.saved = (ledger.DATA, ledger.ROOT, cli.PACKETS, cli.BATCHES, set(evaluate.PILOT_BATCHES))
        ledger.DATA, cli.PACKETS, cli.BATCHES = root / "data", root / "packets", root / "data" / "batches"
        ledger.ROOT = root
        evaluate.PILOT_BATCHES.clear()
        ledger.DATA.mkdir()
        pool = [{"qid": f"pm:{i}", "source": "polymarket", "title": f"Will rocket number {i} launch on time?",
                 "description": "d", "close_time": "2027-01-01T00:00:00+00:00", "url": "u",
                 "market_prob": 0.5, "activity": 1, "fetched_at": "x"} for i in range(36)]
        pool += [{"qid": "pm:senate", "source": "polymarket", "title": "Will the Democrats win the Ohio Senate race?",
                  "description": "d", "close_time": "2027-01-01T00:00:00+00:00", "url": "u", "market_prob": 0.5,
                  "activity": 1, "fetched_at": "x"},
                 {"qid": "pm:ecb", "source": "polymarket", "title": "Will the ECB announce a 25 bps increase?",
                  "description": "d", "close_time": "2027-01-01T00:00:00+00:00", "url": "u", "market_prob": 0.5,
                  "activity": 1, "fetched_at": "x"}]
        (ledger.DATA / "pool.json").write_text(json.dumps(pool))

    def tearDown(self):
        ledger.DATA, ledger.ROOT, cli.PACKETS, cli.BATCHES, pilots = self.saved
        evaluate.PILOT_BATCHES.clear()
        evaluate.PILOT_BATCHES.update(pilots)
        self.tmp.cleanup()

    def _batch(self):
        batch = cli.cmd_batch(["--n", "40", "--seed", "1"])
        return batch, json.loads((cli.PACKETS / batch / "questions.json").read_text())

    def test_eligibility_leaves_out_odds_heavy_topics(self):
        _, packet = self._batch()
        qids = {q["qid"] for q in packet}
        self.assertEqual(len(qids), 36)
        self.assertNotIn("pm:senate", qids)
        self.assertNotIn("pm:ecb", qids)

    def test_record_refuses_double_count_and_logs_exposures(self):
        batch, packet = self._batch()
        runs = cli.PACKETS / batch / "runs"
        leak = packet[0]["qid"]
        rows = [{"qid": q["qid"], "prob": 0.6} for q in packet]
        rows[0].update(saw_market_price=True, exposures=[{"url": "https://news.example/a", "snippet": "odds at 60%",
                                                          "seen_at": "2026-10-28T10:00:00Z"}])
        (runs / "A.json").write_text(json.dumps(rows))
        cli.cmd_record([batch])
        with self.assertRaises(SystemExit):
            cli.cmd_record([batch])
        self.assertEqual(len(ledger.read("final")), 36)
        log = (ledger.DATA / "exposures.csv").read_text()
        self.assertIn("https://news.example/a", log)
        self.assertIn(leak, log)

    def test_v6_is_logodds_mean_of_v1_runs_and_v3_is_exploratory(self):
        batch, packet = self._batch()
        runs = cli.PACKETS / batch / "runs"
        for who, p in (("A", 0.6), ("B", 0.7), ("C", 0.95)):
            (runs / f"{who}.json").write_text(json.dumps([{"qid": q["qid"], "prob": p} for q in packet]))
        (runs / "v3").mkdir()
        (runs / "v3" / "A.json").write_text(json.dumps([{"qid": q["qid"], "prob": 0.9} for q in packet]))
        cli.cmd_record([batch])
        cli.cmd_record([batch, "--variant", "v3"])
        ledger.append("resolutions", [{"qid": q["qid"], "outcome": 1, "resolved_at": "t"} for q in packet])
        s = evaluate.summary()
        ch = {c["variant"]: c for c in s["challengers"]}
        self.assertEqual(ch["v6"]["role"], "challenger")
        self.assertEqual(ch["v6"]["clusters"], 36)
        expected = aggregate.combine([0.6, 0.7, 0.95], "mean_logodds", 1.0)
        self.assertGreater(expected, 0.7)  # log-odds mean is pulled toward the confident run, unlike the median
        self.assertTrue(ch["v6"]["accept"])  # higher than the 0.7 median on 36 YES outcomes
        self.assertEqual(ch["v3"]["role"], "exploratory")
        self.assertFalse(ch["v3"]["accept"])  # exploratory variants never meet the promotion rule
        self.assertNotIn("v6", s["variants"])

    def test_report_json_has_no_nan(self):
        dashboard.write(evaluate.summary())
        text = (ledger.DATA / "report.json").read_text()
        self.assertNotIn("NaN", text)
        json.loads(text)
        self.assertTrue(math.isnan(evaluate.summary()["leak_split"]["v1 clean"]["vs_market"]))


if __name__ == "__main__":
    unittest.main()
