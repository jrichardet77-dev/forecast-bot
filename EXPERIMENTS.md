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
  already in flight finish and are scored as normal. UPDATED 2026-10-28: challengers are now v2 and v6; v3 is
  exploratory and computed without runs (see the owner decision above).
- Practice forecasters use the cheapest adequate Claude model (Haiku) with at most 5 web searches per question.
  From batch 2 on, v1 also runs on Haiku, so v1, v2 and v3 are compared on the same model. Each weekly batch:
  12 questions, 3 runs each of v1, v2 and v3 (9 runs). From 2026-10-28: 3 runs each of v1 and v2 (6 runs); v6 and
  v3c reuse v1's runs.
- If the web-search allowance or usage limits run low, or a run hits a limit, that week's teaching is skipped and the
  daily report says so in one line.
- No new spending. The OpenRouter $25 is only for official forecasts; the live bot changes only after the owner's yes/no.

## Owner decision 2026-10-28: v6 replaces v3 as a challenger (T102 Quinn review, T103 Vesper brief)
Recorded 2026-10-28 from the owner's "Yes" (relayed from the AlmanacBot monitoring session). Practice only; lean
mode, no spending, no live-bot change, nothing on open official questions.

**Champion and challengers (2 challengers):** v1 stays champion. Challengers: v2 (base rates first) and v6
(aggregation). v3 is an exploratory sensitivity check only, never promoted; from batch 2 on it is computed as v3c
(v1's combined forecast capped to 0.10-0.90), so it costs no forecasting runs. v4 and v5 stay shelved.

**v6 pre-registration (written before any v6 score was looked at):** v6 = equal-weight mean in log-odds of the v1
runs each question already has; no new forecasts. No weights and no extremizing now. Weights or extremizing may be
added later only if fitted on earlier clean clusters and judged on held-out clean clusters. Prediction: about 35%
chance v6 reaches the checkpoint ahead of v1; a small effect (+1 to +4 points) if real.

**Primary metric:** paired relative log score of the challenger vs v1 on the same clean question
(100 * ln of the challenger's probability on the outcome over v1's), averaged within each event cluster. Direction:
higher is better. Method: bootstrap over clusters (5,000 resamples). Secondary: Brier score, per-cluster results.

**Stopping rule:**
1. Checkpoint, not promotion: at 30 clean clusters (from batch 2 on, Haiku only), report effect size, 90% interval,
   P(better), cluster count and per-cluster results for each challenger.
2. A challenger that is ahead at the checkpoint with P(better) >= 0.975 (0.95 split over 2 challengers) goes to a
   confirmation stage: the next 20 fresh clean clusters, untouched until then. It must stay ahead there with
   P(better) >= 0.90.
3. Only after confirmation does it go to the owner as a yes/no with its numbers and estimated per-question
   OpenRouter cost. A challenger that misses the checkpoint by 60 clean clusters is dropped and logged.

**Question eligibility (fixed before any further forecasting):** practice batches leave out questions whose title
names an election, race, vote, poll or nominee; a central bank, interest rate or bps move; or a major sports
championship or awards show. News routinely quotes betting odds or market-implied probabilities on these.
Implemented in `fbot/cli.py` (`eligible`); `batch --all-topics` overrides it and is not used for practice. Questions
are never chosen by how forecasts performed.
Amended 2026-10-31, before any forecast of batch 2 (20261031-125505): the word list missed plurals and party/race
wording ("Republicans win Kansas", "votes", "interest rates", "margin of victory", "North Carolina's 9th District",
"mid terms") and awards ("MLS Defender of the Year"). Those words were added and a regression test pins them. Two
draft batches drawn with the old list were deleted unforecast; only the clean draw was kept (7 eligible questions,
not 12, because election week fills the short-horizon pool).

**Exposure log:** each reported exposure is saved with URL, snippet and time in data/exposures.csv. Clean audit:
at each weekly batch, 3 questions marked clean are re-searched by hand for quoted odds. If any shows odds the
forecasters could easily have seen, it is reclassified as exposed and the audit is logged here.

**Model comparability:** from batch 2, v1 and every challenger run on Haiku with the same cutoff, search budget
(5 per question) and scoring. Batch 20261026-221344 stays a separate descriptive pilot and is never pooled.

## Changes from Quinn's review (T102, 2026-10-27), fixed before any challenger result exists
- Questions where any forecaster saw a market price are excluded from every keep/drop decision, acceptance
  statistic and clean count. They stay in a separately labeled diagnostic row ("v1 leaked") and never enter the
  headline score (the headline is "v1 clean").
- Related questions are grouped into event clusters (data/clusters.json), assigned by topic before scoring. New
  batches get cluster IDs when created. Effective sample size is the number of clusters.
- Primary metric: paired relative log score of challenger vs v1 on the same clean question, averaged within each
  cluster. Uncertainty: bootstrap over clusters.
- Promotion rule for challengers: at least 30 clean clusters, mean above 0 and bootstrap P(better) >= 0.975 (0.95
  split across the two live challengers, v2 and v3). Meeting it means "propose to the owner", never automatic.
  Results are reported with effect size, interval and cluster count.
- Batch 20261026-221344 (v1 not on Haiku) is a descriptive pilot only and never counts toward promotion.
- Quinn and Vesper favor replacing v3 with an aggregation challenger built from runs we already make; that swap
  waits on the owner's yes/no (T103).

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
| 2026-10-27 | Quinn T102 changes applied: clean-only judging, event clusters (36 questions, 10 clusters), cluster bootstrap, P>=0.975 with 30 clusters, batch 20261026-221344 kept as pilot | 0 clean | - | rules fixed before results |
| 2026-10-28 | daily check: weekday, no batch (lean mode); 34 practice questions open | 0 clean | - | champion stays |
| 2026-10-28 | owner yes: v6 aggregation replaces v3 as challenger; v3 exploratory (v3c, no runs); eligibility, exposure log, checkpoint plus holdout confirmation pre-registered; record double-count guard and NaN-free report | 0 clean | - | recorded before any v6 score |
| 2026-10-29 | daily check: weekday, no batch (lean mode); 34 practice questions open, 0 newly resolved | 0 clean | - | champion stays |
| 2026-10-30 | daily check: 2 practice questions resolved (ECB October decision, both from the first batch and both exposed); v1 now 4 resolved, all exposed, +1.3 vs market; weekday, no batch (lean mode); 32 open | 0 clean | - | champion stays |
| 2026-10-31 | weekly batch 2 (20261031-125505, 7 questions closing Nov 3-20, Haiku): v1 x3, v2 x3 (v6 and v3c derived). Eligibility list extended first (plurals, party/race wording, awards; two unforecast draft draws deleted). New clusters: anthropic-ipo-2026, france-siege-2026, nato-russia-2026, gta6-2026 (Iran questions join iran-conflict-2026). Exposed: France (v1 B and v2 B, via poly-bets.com) and NATO (v1 A, via polymarket.copilot.markets and polysays.com); those three mirror domains added to the block list. v2 run B says it set base rates after searching, not before (protocol slip, kept and noted). Clean audit: 3 clean questions (Anthropic IPO, GTA 6, Iran ceasefire) re-searched with the block list; no odds in any result | 0 clean (pending) | - | champion stays |
| 2026-10-31 | official: 49 of 110 official questions resolved (48 scored by Metaculus): average peer score +0.8, baseline +25.5; peer score positive on 26 of 48 | - | - | live bot unchanged |
| 2026-11-01 | daily check: 5 practice questions resolved; first clean results: v1 clean on 4 questions in 3 clusters (-12.5 vs market, far too few to read); v6 +0.9 and v3c -2.2 vs v1 on 3 clusters. Checkpoint needs 30 clean clusters | 3 clean | - | champion stays |
| 2026-11-01 | live bot: since Oct 31 15:04 UTC every new official question fails with OpenRouter 402 ("requires more credits, or fewer max_tokens ... can only afford 63436" of 65536 requested; key limit). The $25 prepaid key is nearly spent. No change made: raising the limit is spending and lowering max_tokens is a live-bot change, both need the owner. Official scoring continues (read-only) | - | - | owner decision needed |
| 2026-11-02 | daily check: 2 practice questions resolved; v1 clean now 6 questions in 4 clusters (-9.5 vs market); v6 +0.1 and v3c -1.6 vs v1 on 4 clusters. Live bot still blocked by the OpenRouter key limit: 39 official questions (46289-46401) opened since Oct 31 and none forecast | 4 clean | - | champion stays; owner decision on credits pending |
| 2026-11-03 | daily check: 6 practice questions resolved (incl. the Iran blockade question from batch 2). v1 clean now 11 questions: -7.7 vs market, P(beats market) 0.02, so on clean questions v1 trails the market so far (small sample, 6 clusters). v6 -0.3 and v3c -2.3 vs v1 on 6 clusters. Live bot still blocked: 63 official questions missed since Oct 31 | 6 clean | - | champion stays |
| 2026-11-04 | daily check: 7 practice questions resolved; v1 clean 12 questions -7.5 vs market (P beats market 0.02); v6 -0.1 and v3c -1.6 vs v1 on 6 clusters. 19 practice questions open (below 20), but lean mode allows one batch a week on a weekend and batch 2 ran Oct 31, so the next batch waits for the weekend. Live bot still blocked: 71 official questions missed | 6 clean | - | champion stays |
| 2026-11-05 | daily check: 1 practice question resolved (exposed); v1 clean unchanged at 12. 18 open; weekly batch waits for the weekend (lean mode). Live bot still blocked: 76 official questions missed. Official: 65 of 110 resolved, average peer -0.8, baseline +25.4 | 6 clean | - | champion stays |
| 2026-11-06 | daily check: 1 practice question resolved (clean); v1 clean 13 questions -6.0 vs market (P beats market 0.06); v6 -0.1 and v3c -2.6 vs v1 on 7 clusters. 17 open; weekly batch waits for the weekend. Live bot still blocked: 82 official questions missed | 7 clean | - | champion stays |
| 2026-11-07 | weekly batch 3 (20261107-135350, 12 questions closing Nov 9-26, Haiku): v1 x3, v2 x3 (v6 and v3c derived). Eligibility list extended first ("reelection"; one unforecast draft draw deleted). Clusters: GTA 6, Anthropic IPO, Iran and AI releases join existing clusters; new: nasa-eclipse-stream-2026, microsoft-office-2026, cop31-2026, ecofin-tobacco-2026, t-crb-nova-2026. No forecaster reported a market price. Clean audit: 3 clean questions (Gemini Carbon, ECOFIN tobacco, T CrB) re-searched with the block list; no odds in any result. Official: 67 of 110 resolved, average peer -0.4; live bot still blocked (82 missed) | 7 clean | - | champion stays |
| 2026-11-08 | daily check: no practice question resolved (28 open); v1 clean 14 questions -6.1 vs market. Live bot still blocked: 87 official questions missed | 7 clean | - | champion stays |
| 2026-11-09 | daily check: 1 practice question resolved (a US midterms question from batch 20261018-125311, YES; v1 said 12%, the market was lower). v1 clean now 15 questions, +0.2 vs market (P beats market 0.47): one result moved it from -6.1, so the sample is still far too small. v6 +1.3 and v3c -2.3 vs v1 on 7 clusters. Live bot still blocked: 91 official questions missed | 7 clean | - | champion stays |
| 2026-11-10 | daily check: 2 practice questions resolved (ECOFIN novel tobacco, NO, from batch 3; one older question, NO). v1 clean now 17 questions, -5.9 vs market (P beats market 0.23). v6 +1.9 and v3c -1.5 vs v1 on 8 clusters; v2 +2.9 on 2 clusters (first v2 results, far too few). Live bot still blocked: 97 official questions missed | 8 clean | - | champion stays |
| 2026-11-11 | daily check: 1 practice question resolved (Gemini Carbon release Nov 9-15, YES, AI model releases). v1 clean now 18 questions, -17.2 vs market (P beats market 0.08). v6 +2.0 and v3c -1.5 vs v1 on 8 clusters; v2 +25.0 on 3 clusters (4 questions, far too few; checkpoint needs 30). 24 practice questions open, so no new batch (lean mode: weekend only). Official: 3 more resolved (71 of 110, average peer +0.3, baseline +26.6). Live bot still blocked: 101 official questions missed | 8 clean | - | champion stays |
| 2026-11-12 | daily check: 2 practice questions resolved (T Coronae Borealis nova by Nov 11, NO, batch 20261107; Alaska Senate re-election, NO per Manifold, older batch 20261026). v1 clean now 19 questions, -16.1 vs market (P beats market 0.08). v6 +1.8 and v3c -2.3 vs v1 on 9 clusters; v2 +19.0 on 4 clusters (5 questions; checkpoint needs 30). 22 practice questions open, so no new batch (lean mode: weekend only). Official: no new resolutions (71 of 110). Live bot still blocked: 103 official questions missed | 9 clean | - | champion stays |
| 2026-11-13 | daily check: 1 practice question resolved (Microsoft Office still active on Nov 10, YES, batch 20261107). v1 clean now 20 questions, -15.4 vs market (P beats market 0.09). v6 +1.7 and v3c -2.8 vs v1 on 10 clusters; v2 +15.4 on 5 clusters (6 questions; checkpoint needs 30). 21 practice questions open, so no new batch today (weekly batch due this weekend). Official: no new resolutions (71 of 110). Live bot still blocked: 106 official questions missed | 10 clean | - | champion stays |
