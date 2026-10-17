"""Scoring rules. Log-based scores follow Metaculus's definitions so results translate to the tournament.

- baseline_score: Metaculus binary baseline score, 100 * (log2(p_outcome) + 1). 0 = a 50% forecast; higher is better.
- relative_score: 100 * (ln p_bot - ln p_ref) on the outcome. Metaculus's peer score is this against the mean of other
  forecasters' log scores; we use it against the market price at forecast time (our stand-in for the field).
- brier: (p - outcome)^2, lower is better.
"""
import math
import random

EPS = 1e-4


def _clip(p):
    return min(1 - EPS, max(EPS, float(p)))


def p_outcome(p, outcome):
    p = _clip(p)
    return p if outcome else 1 - p


def brier(p, outcome):
    return (float(p) - (1.0 if outcome else 0.0)) ** 2


def log_score(p, outcome):
    return math.log(p_outcome(p, outcome))


def baseline_score(p, outcome):
    return 100 * (math.log2(p_outcome(p, outcome)) + 1)


def relative_score(p, p_ref, outcome):
    return 100 * (log_score(p, outcome) - log_score(p_ref, outcome))


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def paired_bootstrap(diffs, n=5000, seed=7):
    """Mean of paired differences with a 90% bootstrap interval and P(mean > 0)."""
    diffs = list(diffs)
    if not diffs:
        return {"n": 0, "mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "p_better": float("nan")}
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(mean(rng.choice(diffs) for _ in range(k)) for _ in range(n))
    return {"n": k, "mean": mean(diffs), "lo": means[int(0.05 * n)], "hi": means[int(0.95 * n) - 1],
            "p_better": sum(m > 0 for m in means) / n}
