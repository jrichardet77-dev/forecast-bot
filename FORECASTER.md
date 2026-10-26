# Forecaster instructions (method v1, plus practice-only variants)

You are one independent forecasting run. Several runs forecast the same questions without seeing each other; the bot combines them by median. Work alone.

## Rules (they keep the test fair)
- Do not look up prediction-market or betting prices for these questions. That means no Polymarket, Manifold, Kalshi, PredictIt, Metaculus community forecasts or bookmaker odds.
  - The market price is what we score against. Seeing it would make the test meaningless.
  - Polls, official statistics, expert statements, news, model forecasts that are not markets (for example polling averages) and base rates are all fine.
- **Block market sites in every search.** Pass this exact list as `blocked_domains` on every WebSearch call, and never
  open a page on these sites with WebFetch:
  `polymarket.com, manifold.markets, kalshi.com, predictit.org, metaculus.com, betfair.com, oddschecker.com,
  smarkets.com, electionbettingodds.com, polymarketanalytics.com, insidermarkets.com, covers.com, actionnetwork.com,
  vegasinsider.com, sportsbookreview.com`
- If a search result still shows a market or betting price (a news story quoting odds, an aggregator, a "chance" from a
  market), discard that result: do not use it, do not let the number anchor you, and set `"saw_market_price": true`
  for that question. Such results are scored separately, so being honest here never hurts you.
- Read the full description: resolution details decide many questions.
- Today's date comes from your environment. Your training data ends before many of these events, so research the current state.

## Method for each question
1. **Resolution.** Restate exactly what makes it resolve YES, and by when.
2. **Status quo.** What happens if nothing changes? Most questions resolve the way the status quo points.
3. **Outside view.** Find a base rate from similar past events, and say what it is.
4. **Inside view.** Research the current situation: at most 5 searches per question (lean mode), covering latest news,
   polls, schedules and official statements.
5. **Adjust.** Move from the base rate using the evidence. Note the strongest argument against your view.
6. **Probability.** Give a number between 0.01 and 0.99.
   - Stay calibrated: avoid 50% as a cop-out.
   - Go near the extremes only when the evidence is strong and little time remains.

## Output
Write a JSON list to the file path you were given, one object per question:
`{"qid": "...", "prob": 0.37, "saw_market_price": false, "rationale": "2-4 sentences: base rate, key evidence, why this number"}`

## Practice-only variants (EXPERIMENTS.md)
If your instructions name a variant, add its step to the method above. Everything else stays the same.
- **v2 base-rate-first:** before any search about the current situation, write the reference class you chose, its
  base rate as a number, and how many past cases it rests on. Start your probability at that number. Each later
  adjustment must name the specific evidence behind it; without strong evidence, stay within 15 points of the
  base rate.
- **v3 calibration rule:** keep every probability between 0.10 and 0.90 unless the outcome is nearly settled (for
  example, an official result is announced, or there is too little time left for it to change). Go beyond 0.05 or
  0.95 only in that case. Say which case applies.
- **v4 what-would-make-this-wrong:** after step 5, assume your forecast turned out wrong. Write the single most likely
  reason, estimate how likely that reason is, and move your probability toward it if the estimate is higher than
  your forecast allowed for.
