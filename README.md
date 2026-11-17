# forecast-bot

A forecasting bot being built to compete in Metaculus's AI benchmark tournaments (FutureEval). It is a hobby project, separate from any other business.

## How it works
1. `python3 -m fbot.cli pool` collects open yes/no questions from Polymarket and Manifold (no account needed).
   - Sports, short-term prices and joke markets are filtered out.
2. `python3 -m fbot.cli batch --n 12` picks a diverse set and writes a forecaster packet.
   - The market price is stored separately, so forecasters never see it.
3. Several independent forecaster runs follow `FORECASTER.md` and research each question.
   - The bot takes the median of the runs, the same method as Metaculus's own template bot.
4. `python3 -m fbot.cli record <batch>` stores every run and the final forecast, with the market price at that moment.
5. `python3 -m fbot.cli resolve` checks outcomes; `python3 -m fbot.cli report` scores everything.

## How we measure
- **vs market**: 100 × ln(our probability ÷ market probability) on the actual outcome.
  - This is Metaculus's peer-score formula with the market standing in for the other forecasters.
  - Above 0 means we beat the market.
- **Baseline score**: Metaculus's own scale; 0 = always saying 50%.
- **Brier**: squared error; lower is better.
- **Changes**: kept only when they beat the current champion on the same questions (rule in EXPERIMENTS.md).

## Status
- **Retired (November 17, 2026). We are no longer participating.**
  - AlmanacBot competed in the Fall 2026 Metaculus FutureEval bot tournament from October 17, 2026.
  - He stopped forecasting when the $25 of prepaid OpenRouter credit ran out. The owner decided not to add more.
  - Final standing at retirement: 110 questions predicted, 70 scored, average peer score 0.26.
- Forecasts already submitted stay on Metaculus and will be scored as their questions resolve.
- The scheduled Forecast workflow is turned off: it no longer runs on a timer and never submits.
- The daily practice check is switched off.
- The read-only Official scores job still runs once a day, so final results keep being recorded.

Tests: `python3 tests/test_core.py`
