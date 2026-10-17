"""Combine several independent forecasts of one question, and post-process the result.

Post-processing is where cheap, testable improvements live: each transform below is a named variant that the
evaluation can switch on or off against the same recorded raw forecasts (see fbot/evaluate.py).
"""
import math
import statistics


def logit(p):
    p = min(1 - 1e-6, max(1e-6, p))
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def median(ps):
    return statistics.median(ps)


def mean_logodds(ps):
    return sigmoid(statistics.mean(logit(p) for p in ps))


def extremize(p, a):
    """a > 1 pushes away from 50%; a < 1 shrinks toward 50% (done in log-odds)."""
    return sigmoid(a * logit(p))


def clamp(p, lo=0.01, hi=0.99):
    return min(hi, max(lo, p))


AGGREGATORS = {"median": median, "mean_logodds": mean_logodds}


def combine(ps, method="median", a=1.0, lo=0.01, hi=0.99):
    return clamp(extremize(AGGREGATORS[method](ps), a), lo, hi)
