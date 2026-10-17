# Competition research (2026-10-17)

Labels:
- **VERIFIED**: the page was opened, and the URL is given.
- **SNIPPET**: search text only.
- **Main source:** the FutureEval resources page, https://www.metaculus.com/notebooks/38928/ai-benchmark-resources/ ("Edited on Oct 16, 2026").
- **Blocked:** the tournament pages themselves returned Cloudflare 403.

## Rules that shape the design

**Tournaments** (VERIFIED):
- The Fall 2026 bot tournament has a $50k pool and about 300–400 questions. Its id is `fall-futureeval-2026` (33121).
- MiniBench pays $1k every two weeks, with about 60 questions written and resolved by an LLM.
- `bot-testing-area` is unscored and has one question of each type.

**Question types:** binary, numeric, discrete and multiple choice.
- Numeric forecasts are a 201-point CDF.
- Each step must rise by at least 0.0005, and no single step may exceed 0.2.

**Timing** (VERIFIED):
- Questions open at random hours and stay open for 3 hours, usually 5 or fewer at a time.
- Submit one forecast per question; only the last one before close counts.
- Unforecast questions score 0. The template polls every 20 minutes; we poll every 30.

**Eligibility** (VERIFIED, rules page https://www.metaculus.com/notebooks/28751/q1-ai-forecasting-benchmark-rules/):
- One prize-eligible bot per person; entrants must be 18 or older.
- Prize winners verify their identity and agree to a code inspection.

**No human in the loop** (VERIFIED):
- The bot maker may not preview the bot's forecasts on open questions and then adjust them, or re-run it because they dislike a forecast.
- No copy-pasting forecasts by hand. Each forecast needs a private comment.
- Our design follows this: practice runs use Polymarket and Manifold questions, never open Metaculus tournament questions.

**Registration:**
- A human creates the account, then makes a bot under "My Forecasting Bots" and copies its token.
- Everyone fills in the participation form (https://forms.gle/aQdYMq9Pisrf1v7d8). The same form applies for free LLM credits.

**Free resources** (VERIFIED):
- **LLM credits:** OpenRouter credits donated by OpenAI, Anthropic and Google.
  - About $100 to start, more for above-average MiniBench performance.
  - Open-source bots get 2.5x.
- **AskNews:** free news search for registered bot makers (1k calls a month).

**Scoring:**
- Spot peer score, log-based (VERIFIED).
- A bot's prize "take" is the square of its question-weighted summed peer score, or 0 if negative (VERIFIED).
- Take ÷ all takes = pool share (SNIPPET).

**Payout:**
- By bank transfer through Ramp, only after every question of the season resolves and the survey is done.
- Fall 2026 prizes are therefore likely around February–March 2027 (inference).

## What wins (VERIFIED, Metaculus analyses)

**Bots vs professional forecasters** (0 = equal):
| Season | Bot team vs Pros |
|---|---|
| Q2 2025 | -20.0 |
| Spring 2026 | -1.25 (95% CI -4.9 to 2.4) |

Spring 2026: https://www.metaculus.com/notebooks/45373/spring-2026-futureeval-analysis/

**Spring 2026 results:**
- 173 bots took part; the top-10 averaged spot peer scores of 13.2–18.9.
- All top-10 survey respondents used GPT-5.2 or newer.
- 7 of the top 10 bot makers were hobbyists.

**Strongest levers** (https://www.metaculus.com/notebooks/43363/overview-of-ai-forecasting-research/):
- A frontier model.
- Scaffolding, worth +5 to 11 peer points per question.
- Several research sources (r = 0.42).
- An ensemble of 3–7 runs across model families (86% of Fall 2025 winners used one).
- Capping predictions away from 0% and 100%.
- Explicit base rates.
- Looking up similar resolved questions.

**Mixed or harmful** (bot-maker advice, https://www.metaculus.com/notebooks/45336/bot-maker-advice-spring-2026/):
- Extremizing was rolled back by several bot makers.
- Complexity: one bot fell from 20th to about 63rd after adding logit aggregation, extremization and crowd blending.
- Persona prompts and "Bayesian" prompts didn't help.

**Biggest avoidable losses:**
- Edge cases in resolution criteria.
- Metaculus's "assume it hasn't happened yet" convention. One maker lost 90 points by not telling the bot.

**Past winners:**
- Q4 2024: pgodzinai.
- Q1 2025: Metaculus's own template bot.
- Q2 2025: Panshul42, open source, with outside-view and inside-view reports and 5 predictions across models.
- Top open-source bot: nostreambot (median ensemble plus AskNews).

## Testing without leakage
- Models cannot reliably "forget" what they know. Search results leak outcomes, so backtests look better than reality.
- **Our approach:** forward tests on live questions that resolve after today, scored against the market price at the moment of forecasting.
- **Leak found in practice:** search results sometimes show market prices unasked. Those questions are flagged in `data/exposed.json` and reported separately.

## Test run, 2026-10-17 (unscored test area, nothing submitted)
- The Metaculus bot token works: the bot fetched 9 test questions (for example https://www.metaculus.com/questions/45517).
- Every forecast failed because the old free Metaculus LLM proxy is gone. `llm-proxy.metaculus.com` no longer resolves in DNS (checked from GitHub Actions and from the development container).
- Free LLM credit requests for Fall 2026 are closed. The participation form says applications reopen a few weeks before the next season.
- Result: no free AI route exists until the credits reopen. Running now needs a paid API key, which is an owner spending decision.
