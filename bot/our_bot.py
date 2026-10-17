"""Our competition bot: Metaculus's Fall 2026 template with our forecasting method and aggregation.

The template (bot/template/, copied unchanged from github.com/Metaculus/metac-bot-template at commit 096cb20,
2026-10-15) handles the Metaculus API, research, multiple-choice and numeric formats. We override:
  - the binary prompt (method v1 from FORECASTER.md plus Metaculus's resolution conventions);
  - which model each of the N runs uses (round-robin over BOT_MODELS, for an ensemble across model families);
  - binary aggregation (our champion rule from fbot/evaluate.py: median, clamped to 1-99%).
"""
import itertools
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bot" / "template"))
sys.path.insert(0, str(ROOT))

from forecasting_tools import (BinaryPrediction, BinaryQuestion, GeneralLlm, ReasonedPrediction,  # noqa: E402
                               clean_indents, structure_output)

from fbot import aggregate, evaluate  # noqa: E402
from template_main import FallTemplateBot2026  # noqa: E402

# Comma-separated OpenRouter model names, e.g. "openrouter/openai/gpt-5.4,openrouter/anthropic/claude-sonnet-4.5".
# Set in the workflow once Metaculus confirms which models our credits cover.
DEFAULT_MODELS = "openrouter/openai/gpt-4o"

BINARY_METHOD = """
Work through these steps before answering:
(a) Resolution: restate exactly what makes this resolve YES, and the deadline. Note any fine print that could
    decide it. Metaculus convention: if something has not been reported as happening yet, assume it has not happened.
(b) Time left until the outcome is known.
(c) Status quo: the outcome if nothing changes. Most questions resolve the way the status quo points.
(d) Outside view: a base rate from comparable past events; state the number and the reference class.
(e) Inside view: what the research says about this specific case, and how it moves you from the base rate.
(f) The strongest argument for the opposite outcome.
Then give a calibrated probability. Avoid 50% as a default; go near 1% or 99% only with strong evidence and
little time left.
"""


class OurBot(FallTemplateBot2026):
    def __init__(self, *args, models=None, **kwargs):
        super().__init__(*args, **kwargs)
        names = [m.strip() for m in (models or os.environ.get("BOT_MODELS", DEFAULT_MODELS)).split(",") if m.strip()]
        self.forecast_models = [GeneralLlm(model=m, temperature=0.4, timeout=120, allowed_tries=2) for m in names]
        self._model_cycle = itertools.cycle(range(len(self.forecast_models)))

    def next_model(self):
        return self.forecast_models[next(self._model_cycle)]

    def binary_prompt(self, question: BinaryQuestion, research: str) -> str:
        return clean_indents(f"""
            You are an expert forecaster competing in a forecasting tournament scored by log score.

            Question: {question.question_text}

            Background:
            {question.background_info}

            Resolution criteria (not yet satisfied):
            {question.resolution_criteria}

            {question.fine_print}

            Research notes:
            {research}

            Today is {datetime.now().strftime("%Y-%m-%d")}.
            {BINARY_METHOD}
            {self._get_conditional_disclaimer_if_necessary(question)}
            The last thing you write is your final answer as: "Probability: ZZ%", 0-100
            """)

    async def _run_forecast_on_binary(self, question: BinaryQuestion, research: str) -> ReasonedPrediction[float]:
        model = self.next_model()
        reasoning = await model.invoke(self.binary_prompt(question, research))
        pred: BinaryPrediction = await structure_output(
            reasoning, BinaryPrediction, model=self.get_llm("parser", "llm"),
            num_validation_samples=self._structure_output_validation_samples,
            additional_instructions=clean_indents(f"""
                The text given to you is trying to give a probability forecast for a binary question.
                {self._create_resolved_question_parsing_message()}"""))
        p = max(0.01, min(0.99, pred.prediction_in_decimal))
        return ReasonedPrediction(prediction_value=p, reasoning=f"[{model.model}]\n{reasoning}")

    async def _aggregate_predictions(self, predictions, question):
        if isinstance(question, BinaryQuestion):
            champ = evaluate.CHAMPION
            return aggregate.combine([float(p) for p in predictions], champ["method"], champ["a"])
        return await super()._aggregate_predictions(predictions, question)
