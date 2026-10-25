"""Question sources, normalized to one shape.

Question: {qid, source, title, description, close_time (ISO, UTC), url, market_prob, activity, fetched_at}
Resolution: {qid, outcome (1, 0, or None for annulled), resolved_at}

Manifold and Polymarket need no account. Metaculus needs METACULUS_TOKEN (owner approval required to create one).
"""
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "forecast-bot research (non-commercial)", "Accept": "application/json"}


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _iso(ms_or_str):
    if isinstance(ms_or_str, (int, float)):
        return dt.datetime.fromtimestamp(ms_or_str / 1000, dt.timezone.utc).isoformat(timespec="seconds")
    return dt.datetime.fromisoformat(ms_or_str.replace("Z", "+00:00")).astimezone(dt.timezone.utc).isoformat(
        timespec="seconds")


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# Markets that are not Metaculus-style questions: sports fixtures, short-term prices, weather, personal or joke markets.
EXCLUDE = re.compile(
    r"\b(vs\.?|v\.|o/u|over/under|spread|up or down|price of|above \$|below \$|reach \$|dip to|fdv|"
    r"temperature|nfl|nba|mlb|nhl|ufc|wnba|premier league|la ?liga|serie a|bundesliga|champions league|"
    r"grand prix|tennis|worlds 20|esports|world series|championship series|super bowl|stanley cup|nba finals|playoffs|mvp|open:|match|game \d|map \d|kills|goals|touchdowns|coinflip|my |i will|will i )",
    re.I)


def eligible_title(title):
    return not EXCLUDE.search(title or "")


# ---------------------------------------------------------------- Manifold
MANIFOLD = "https://api.manifold.markets/v0"


def manifold_open(min_days=2, max_days=45, min_bettors=20, limit=500):
    data = _get(f"{MANIFOLD}/search-markets?" + urllib.parse.urlencode(
        {"term": "", "filter": "open", "contractType": "BINARY", "sort": "score", "limit": limit}))
    now = dt.datetime.now(dt.timezone.utc).timestamp() * 1000
    out = []
    for m in data:
        if m.get("uniqueBettorCount", 0) < min_bettors or not eligible_title(m["question"]):
            continue
        if not now + min_days * 864e5 < m.get("closeTime", 0) < now + max_days * 864e5:
            continue
        out.append({"qid": f"mf:{m['id']}", "source": "manifold", "title": m["question"].strip(),
                    "description": "", "close_time": _iso(m["closeTime"]), "url": m["url"],
                    "market_prob": round(m["probability"], 4), "activity": m["uniqueBettorCount"],
                    "fetched_at": now_iso()})
    return out


def manifold_details(market_id):
    m = _get(f"{MANIFOLD}/market/{market_id}")
    return (m.get("textDescription") or "").strip()


def manifold_resolution(market_id):
    m = _get(f"{MANIFOLD}/market/{market_id}")
    if not m.get("isResolved"):
        return None
    r = m.get("resolution")
    outcome = {"YES": 1, "NO": 0}.get(r)  # MKT (partial) and CANCEL are treated as annulled
    return {"qid": f"mf:{market_id}", "outcome": outcome, "resolved_at": _iso(m.get("resolutionTime") or 0),
            "note": r}


# ---------------------------------------------------------------- Polymarket
GAMMA = "https://gamma-api.polymarket.com"


def _pm_prices(m):
    try:
        outcomes, prices = json.loads(m["outcomes"]), [float(x) for x in json.loads(m["outcomePrices"])]
    except (KeyError, ValueError, TypeError):
        return None, None
    return outcomes, prices


def polymarket_open(min_days=2, max_days=45, min_volume=100_000, pages=4):
    now = dt.datetime.now(dt.timezone.utc)
    out = []
    for page in range(pages):
        data = _get(f"{GAMMA}/markets?" + urllib.parse.urlencode(
            {"closed": "false", "limit": 100, "offset": 100 * page, "order": "volumeNum", "ascending": "false",
             "end_date_min": (now + dt.timedelta(days=min_days)).isoformat(),
             "end_date_max": (now + dt.timedelta(days=max_days)).isoformat()}))
        for m in data:
            outcomes, prices = _pm_prices(m)
            if outcomes != ["Yes", "No"] or float(m.get("volume") or 0) < min_volume:
                continue
            if not eligible_title(m["question"]) or not 0.01 < prices[0] < 0.99:
                continue
            out.append({"qid": f"pm:{m['id']}", "source": "polymarket", "title": m["question"].strip(),
                        "description": (m.get("description") or "").strip(), "close_time": _iso(m["endDate"]),
                        "url": f"https://polymarket.com/market/{m['slug']}", "market_prob": round(prices[0], 4),
                        "activity": round(float(m["volume"])), "fetched_at": now_iso()})
        if len(data) < 100:
            break
    return out


def polymarket_resolution(market_id):
    m = _get(f"{GAMMA}/markets/{market_id}")
    outcomes, prices = _pm_prices(m)
    if not m.get("closed") or m.get("umaResolutionStatus") not in (None, "resolved") or prices is None:
        return None
    if prices[0] >= 0.99:
        outcome = 1
    elif prices[0] <= 0.01:
        outcome = 0
    else:
        return None
    return {"qid": f"pm:{market_id}", "outcome": outcome, "resolved_at": _iso(m.get("closedTime") or m["endDate"])
            if m.get("closedTime") else _iso(m["endDate"]), "note": "uma resolved"}


# ---------------------------------------------------------------- Metaculus (token required)
METACULUS = "https://www.metaculus.com/api"


def metaculus_token():
    tok = (os.environ.get("METACULUS_TOKEN") or "").strip()
    if not tok:
        raise RuntimeError("METACULUS_TOKEN is not set (needs the owner's approval to create a bot account).")
    return tok


def metaculus_open(tournament, limit=100):
    data = _get(f"{METACULUS}/posts/?" + urllib.parse.urlencode(
        {"limit": limit, "tournaments": tournament, "statuses": "open", "include_description": "true",
         "forecast_type": "binary,multiple_choice,numeric,discrete"}, doseq=True),
        {"Authorization": f"Token {metaculus_token()}"})
    out = []
    for post in data.get("results", []):
        q = post.get("question")
        if not q:
            continue
        out.append({"qid": f"mc:{q['id']}", "source": "metaculus", "post_id": post["id"], "type": q.get("type"),
                    "title": q["title"], "description": q.get("description", ""),
                    "resolution_criteria": q.get("resolution_criteria", ""), "fine_print": q.get("fine_print", ""),
                    "close_time": q.get("scheduled_close_time"), "url": f"https://www.metaculus.com/questions/{post['id']}/",
                    "market_prob": None, "activity": None, "fetched_at": now_iso()})
    return out


def resolution(qid):
    src, ident = qid.split(":", 1)
    if src == "mf":
        return manifold_resolution(ident)
    if src == "pm":
        return polymarket_resolution(ident)
    raise ValueError(f"no resolver for {qid}")


def current_prob(qid):
    src, ident = qid.split(":", 1)
    if src == "mf":
        return round(_get(f"{MANIFOLD}/market/{ident}")["probability"], 4)
    if src == "pm":
        _, prices = _pm_prices(_get(f"{GAMMA}/markets/{ident}"))
        return round(prices[0], 4) if prices else None
    return None
