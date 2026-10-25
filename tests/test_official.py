import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fbot import official  # noqa: E402

MC_PRED = ("predicted_options=[PredictedOption(option_name='Labour-led', probability=0.46799999999999997), "
           "PredictedOption(option_name='National-led', probability=0.462), "
           "PredictedOption(option_name='None before January', probability=0.07)]")


def post(status="resolved", resolution="yes", score_data=None, resolved_at="2026-10-26T10:00:00Z"):
    q = {"title": "Will it happen?", "status": status, "resolution": resolution,
         "actual_resolve_time": resolved_at if status == "resolved" else None}
    if score_data is not None:
        q["my_forecasts"] = {"latest": {}, "history": [], "score_data": score_data}
    return {"id": 1, "question": q}


class Parsing(unittest.TestCase):
    def test_post_id_and_options(self):
        self.assertEqual(official.post_id("https://www.metaculus.com/questions/46045"), "46045")
        self.assertEqual(official.post_id("https://www.metaculus.com/questions/46045/"), "46045")
        opts = official.parse_options(MC_PRED)
        self.assertEqual(list(opts), ["Labour-led", "National-led", "None before January"])
        self.assertAlmostEqual(opts["National-led"], 0.462)

    def test_cut_off_options_text_keeps_complete_entries(self):
        self.assertEqual(len(official.parse_options(MC_PRED[:150])), 1)

    def test_latest_published_forecast_wins(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "official.csv"
            with p.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["at", "question_url", "type", "prediction", "published", "error"])
                w.writerow(["t1", "https://www.metaculus.com/questions/7", "BinaryQuestion", "0.3", "True", ""])
                w.writerow(["t2", "https://www.metaculus.com/questions/7", "BinaryQuestion", "0.6", "True", ""])
                w.writerow(["t3", "https://www.metaculus.com/questions/7", "BinaryQuestion", "0.9", "False", ""])
            self.assertEqual(official.latest_forecasts(p)["7"]["prediction"], "0.6")


class LocalScore(unittest.TestCase):
    def test_binary_baseline_matches_metaculus(self):
        self.assertAlmostEqual(official.local_baseline("BinaryQuestion", "0.5", "yes"), 0)
        self.assertAlmostEqual(official.local_baseline("BinaryQuestion", "0.25", "yes"), -100)
        self.assertAlmostEqual(official.local_baseline("BinaryQuestion", "0.25", "no"), 58.5)

    def test_multiple_choice_baseline(self):
        s = official.local_baseline("MultipleChoiceQuestion", MC_PRED, "National-led")
        self.assertAlmostEqual(s, round(100 * (official.math.log(3 * 0.462) / official.math.log(3)), 1))

    def test_unscored_cases(self):
        self.assertIsNone(official.local_baseline("BinaryQuestion", "0.4", "annulled"))
        self.assertIsNone(official.local_baseline("NumericQuestion", "declared_percentiles=[...]", "12.5"))
        self.assertIsNone(official.local_baseline("MultipleChoiceQuestion", MC_PRED, "Other"))


class Rows(unittest.TestCase):
    ours = {"type": "BinaryQuestion", "prediction": "0.8"}

    def test_metaculus_scores_preferred(self):
        r = official.score_row("5", post(score_data={"peer_score": 12.34, "baseline_score": 67.8}), self.ours)
        self.assertEqual((r["status"], r["peer_score"], r["baseline_score"], r["score_source"]),
                         ("resolved", 12.3, 67.8, "metaculus"))
        self.assertEqual(r["resolved_at"], "2026-10-26")

    def test_falls_back_to_local_baseline(self):
        r = official.score_row("5", post(score_data={}), self.ours)
        self.assertEqual((r["peer_score"], r["score_source"]), ("", "computed locally"))
        self.assertAlmostEqual(r["baseline_score"], 67.8)

    def test_open_question_has_no_score(self):
        r = official.score_row("5", post(status="open", resolution=None), self.ours)
        self.assertEqual((r["status"], r["baseline_score"], r["score_source"]), ("open", "", ""))

    def test_update_skips_resolved_and_summarizes(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            src = d / "official.csv"
            with src.open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["at", "question_url", "type", "prediction", "published", "error"])
                w.writerow(["t", "https://www.metaculus.com/questions/1", "BinaryQuestion", "0.8", "True", ""])
                w.writerow(["t", "https://www.metaculus.com/questions/2", "BinaryQuestion", "0.3", "True", ""])
            calls = []

            def fetch(pid):
                calls.append(pid)
                return post(score_data={"peer_score": 10, "baseline_score": 50}) if pid == "1" else \
                    post(status="open", resolution=None)

            sp = d / "s.csv"
            self.assertEqual(official.update(fetch=fetch, pause=0, official_path=src, scores_path=sp), (2, 1))
            # the resolved question is not fetched again
            self.assertEqual(official.update(fetch=fetch, pause=0, official_path=src, scores_path=sp), (1, 1))
            s = official.summary(official.read_scores(sp))
            self.assertEqual(calls, ["1", "2", "2"])
            self.assertEqual((s["tracked"], s["resolved"], s["avg_peer_score"]), (2, 1, 10.0))
            self.assertIn("1 of 2 official questions resolved", official.summary_text(s))

    def test_empty_state_text(self):
        self.assertEqual(official.summary_text(official.summary({})), "No official questions resolved yet.")



if __name__ == "__main__":
    unittest.main()
