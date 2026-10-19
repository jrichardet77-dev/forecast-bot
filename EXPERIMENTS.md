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

## Log
| Date | Change | Questions resolved | Result | Decision |
|---|---|---|---|---|
| 2026-10-17 | v1 baseline, batch 20261017-1423 (12 questions) | 0 | pending | champion |
| 2026-10-18 | v1, batch 20261018-125311 (12 questions; 5 had market prices in search results, ignored by the forecasters and logged in data/exposed.json) | 0 | pending | champion stays (fewer than 30 resolved) |
| 2026-10-19 | daily check: no new batch (24 practice questions open) | 0 | pending | champion stays (fewer than 30 resolved) |
