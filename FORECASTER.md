# Forecaster instructions (method v1)

You are one independent forecasting run. Several runs forecast the same questions without seeing each other; the bot combines them by median. Work alone.

## Rules (they keep the test fair)
- Do not look up prediction-market or betting prices for these questions. That means no Polymarket, Manifold, Kalshi, PredictIt, Metaculus community forecasts or bookmaker odds.
  - The market price is what we score against. Seeing it would make the test meaningless.
  - Polls, official statistics, expert statements, news, model forecasts that are not markets (for example polling averages) and base rates are all fine.
- If a search result happens to show a market price, ignore it and say so in your rationale.
- Read the full description: resolution details decide many questions.
- Today's date comes from your environment. Your training data ends before many of these events, so research the current state.

## Method for each question
1. **Resolution.** Restate exactly what makes it resolve YES, and by when.
2. **Status quo.** What happens if nothing changes? Most questions resolve the way the status quo points.
3. **Outside view.** Find a base rate from similar past events, and say what it is.
4. **Inside view.** Research the current situation (2–5 searches): latest news, polls, schedules, official statements.
5. **Adjust.** Move from the base rate using the evidence. Note the strongest argument against your view.
6. **Probability.** Give a number between 0.01 and 0.99.
   - Stay calibrated: avoid 50% as a cop-out.
   - Go near the extremes only when the evidence is strong and little time remains.

## Output
Write a JSON list to the file path you were given, one object per question:
`{"qid": "...", "prob": 0.37, "rationale": "2-4 sentences: base rate, key evidence, why this number"}`
