"""Run the competition bot.

  python bot/run.py --mode test_questions     forecast the unscored bot-testing-area (needs METACULUS_TOKEN)
  python bot/run.py --mode tournament         forecast open Fall FutureEval + MiniBench questions

Nothing is submitted unless BOT_PUBLISH=yes is set. That switch is turned on only after the owner approves an
official entry and the competition rules have been re-checked.
"""
import argparse
import asyncio
import csv
import datetime as dt
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bot"))
sys.path.insert(0, str(ROOT / "bot" / "template"))

from bot_helpers import check_environment  # noqa: E402
from forecasting_tools import MetaculusClient  # noqa: E402
from our_bot import OurBot  # noqa: E402

LOGS = {"tournament": ROOT / "data" / "official.csv", "test_questions": ROOT / "data" / "test-runs.csv"}


def log_reports(reports, published, mode):
    LOG = LOGS[mode]
    LOG.parent.mkdir(exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["at", "question_url", "type", "prediction", "published", "error"])
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        for r in reports:
            if isinstance(r, BaseException):
                w.writerow([now, "", "", "", published, f"{type(r).__name__}: {str(r)[:200]}"])
            else:
                w.writerow([now, r.question.page_url, type(r.question).__name__, str(r.prediction)[:300], published, ""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["tournament", "test_questions"], default="test_questions")
    mode = ap.parse_args().mode
    publish = os.environ.get("BOT_PUBLISH") == "yes" and mode == "tournament"
    check_environment(strict=True)
    bot = OurBot(research_reports_per_question=1, predictions_per_research_report=5,
                 use_research_summary_to_forecast=False, publish_reports_to_metaculus=publish,
                 folder_to_save_reports_to=None, skip_previously_forecasted_questions=(mode == "tournament"),
                 extra_metadata_in_explanation=True)
    client = MetaculusClient()
    targets = ([client.CURRENT_AI_COMPETITION_ID, client.CURRENT_MINIBENCH_ID] if mode == "tournament"
               else ["bot-testing-area"])
    reports = []
    for t in targets:
        reports += asyncio.run(bot.forecast_on_tournament(t, return_exceptions=True))
    log_reports(reports, publish, mode)
    bot.log_report_summary(reports)
    print(f"{'PUBLISHED' if publish else 'DRY RUN (nothing submitted)'}: {len(reports)} questions")


if __name__ == "__main__":
    main()
