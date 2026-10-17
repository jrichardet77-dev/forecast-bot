"""Competition bot, end to end with a fake model and a hand-made Metaculus question (no network, no token).
Runs only where forecasting-tools is installed (the bot's own environment)."""
import asyncio
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bot"))
try:
    import our_bot
    from forecasting_tools import BinaryPrediction, BinaryQuestion, GeneralLlm
except ImportError:  # pragma: no cover
    our_bot = None


@unittest.skipIf(our_bot is None, "forecasting-tools not installed")
class BotSmoke(unittest.TestCase):
    def test_binary_ensemble_rotates_models_and_takes_median(self):
        seen, answers = [], iter(["Probability: 20%", "Probability: 35%", "Probability: 30%",
                                  "Probability: 90%", "Probability: 25%"])

        async def fake_invoke(self, prompt):
            if "Probability: ZZ%" not in prompt:  # research summary and other helper calls
                return "summary"
            seen.append((self.model, prompt))
            return next(answers)

        async def fake_structure(text, cls, **kw):
            return BinaryPrediction(prediction_in_decimal=int(re.findall(r"(\d+)%", text)[-1]) / 100)

        GeneralLlm.invoke, our_bot.structure_output = fake_invoke, fake_structure
        bot = our_bot.OurBot(models="openrouter/a/model-1,openrouter/b/model-2", research_reports_per_question=1,
                             predictions_per_research_report=5, publish_reports_to_metaculus=False,
                             llms={"default": "openrouter/a/model-1", "parser": "openrouter/a/model-1",
                                   "researcher": "no_research", "summarizer": "openrouter/a/model-1"})
        q = BinaryQuestion(question_text="Will X happen by 2026-12-31?", background_info="bg",
                           resolution_criteria="YES if X is reported.", fine_print="", page_url="https://example.org/q/1",
                           id_of_question=1, id_of_post=1)
        report = asyncio.run(bot.forecast_question(q))
        self.assertAlmostEqual(report.prediction, 0.30)  # median of 20, 35, 30, 90, 25
        models = [m for m, _ in seen]
        self.assertEqual(models, ["openrouter/a/model-1", "openrouter/b/model-2"] * 2 + ["openrouter/a/model-1"])
        self.assertIn("Outside view", seen[0][1])
        self.assertIn("assume it has not happened", seen[0][1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
