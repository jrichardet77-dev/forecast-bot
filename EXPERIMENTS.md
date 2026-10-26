# Experiments

## Rule for keeping a change
A challenger replaces the champion only when all of these hold on the same resolved questions:
- its mean relative log score vs the champion is above 0;
- the paired bootstrap probability that it is better is at least 0.90;
- at least 30 questions have resolved.

Until then the champion stays. A failed change is recorded here, not deleted.

## Champion
- **v1** (2026-10-17): FORECASTER.md method v1 (resolution, status quo, base rate, research, adjust).
  - 3 independent runs, median, clamped to 1–99%.

## Queued challengers
Post-processing challengers are scored automatically from the recorded runs, with no extra forecasting:
- mean of log-odds instead of median;
- extremizing ×1.3;
- shrinking ×0.8;
- mean of log-odds plus extremizing ×1.3.

## Lean mode (owner decision 2026-10-26, relayed from the "AlmanacBot monitoring" session)
Teaching never takes from Fourth & Found work.
- At most 1 new practice batch per week, run during the daily check on a weekend or at off-hours. No extra batches.
- Only v2 (base rate first) and v3 (calibration 0.10-0.90) are tested. v4 and v5 are SHELVED (below); questions
  already in flight finish and are scored as normal.
- Practice forecasters use the cheapest adequate Claude model (Haiku) with at most 5 web searches per question.
  From batch 2 on, v1 also runs on Haiku, so v1, v2 and v3 are compared on the same model. Each weekly batch:
  12 questions, 3 runs each of v1, v2 and v3 (9 runs).
- If the web-search allowance or usage limits run low, or a run hits a limit, that week's teaching is skipped and the
  daily report says so in one line.
- No new spending. The OpenRouter $25 is only for official forecasts; the live bot changes only after the owner's yes/no.

## Pre-registered 2026-10-26 (practice only; owner-approved teaching plan)
Each challenger runs on the same practice questions as v1, judged only on questions where no forecaster saw a market
price, with the rule above (n >= 30, mean vs champion > 0, P(better) >= 0.90). Predictions are written before any
result is known. A variant that meets the rule goes to the owner as a yes/no with its numbers and its estimated
per-question OpenRouter cost; the live bot's prompts, models and settings are never changed here.

| Variant | What changes | Prediction (2026-10-26) | Keep / drop |
|---|---|---|---|
| v2 base-rate-first | reference class and numeric base rate written before any current-news search; adjustments need named evidence | small gain: about 30% chance it meets the rule within 60 resolved questions | meets the rule: propose to owner; else drop at 60 resolved |
| v3 calibration rule | probabilities kept within 0.10-0.90 unless the outcome is nearly settled | small or no gain vs market, but fewer large losses; about 25% chance it meets the rule | as above |
| v4 what-would-make-this-wrong | a pre-mortem step before the final number | about 20% chance it meets the rule; may help most on long-shot YES questions | SHELVED: lean mode, owner 2026-10-26 (batch 20261026-221344 still scored) |
| v5 five forecasters | median of 5 independent v1 runs instead of 3 | about 35% chance it meets the rule; cheapest to adopt if it does (2 more runs per question) | SHELVED: lean mode, owner 2026-10-26 (batch 20261026-221344 still scored) |

How they run: Claude subagents on short-horizon practice batches (closing within 1-3 weeks, `batch --max-days 21`).
v1 runs go in packets/<batch>/runs/, each challenger in packets/<batch>/runs/<variant>/. v5 is recorded with
`record <batch> --variant v5 --with v1`, so it uses v1's three runs plus two more.

## Log
| Date | Change | Questions resolved | Result | Decision |
|---|---|---|---|---|
| 2026-10-17 | v1 baseline, batch 20261017-1423 (12 questions) | 0 | pending | champion |
| 2026-10-18 | v1, batch 20261018-125311 (12 questions; 5 had market prices in search results, ignored by the forecasters and logged in data/exposed.json) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-19 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-20 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-21 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-22 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-23 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-24 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-25 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-26 | first 2 practice questions resolved (both had market prices leak into search; see data/exposed.json) | 2 | v1 vs market +8.4 (90% interval -21.1 to +37.8) | champion stays (fewer than 30 resolved) |
| 2026-10-26 | batch 20261026-221344 (12 questions closing by Nov 16): v1 x3, v2/v3/v4 x3 each, v5 = v1 + 2 more runs; market sites blocked in every search, yet 8 of 12 questions still had a price reach some forecaster (news quoting odds), so only 4 are clean | 2 (earlier batches) | pending | champion stays |
| 2026-10-26 | owner decision: lean mode (1 batch a week, v2 and v3 only, Haiku forecasters, at most 5 searches per question); v4 and v5 shelved | - | - | recorded |
