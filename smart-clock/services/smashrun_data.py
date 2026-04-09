"""
SmashRun data provider.
Uses the SmashRun API with a personal access token.
Token is read from .env file (SMASHRUN_TOKEN).
Falls back to mock data if no token or API is unreachable.
"""

import os
import time
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

import config

load_dotenv()

_cache = None
_cache_time = 0

SMASHRUN_TOKEN = os.environ.get("SMASHRUN_TOKEN", "")
API_BASE = "https://api.smashrun.com/v1"
KM_TO_MILES = 0.621371

MOCK_DATA = {
    "total_miles": 12.4,
    "num_runs": 3,
    "avg_pace": "8:42",
    "daily": [3.1, 0.0, 5.2, 0.0, 4.1, 0.0, 0.0],
}


def _format_pace(total_seconds, total_miles):
    if total_miles <= 0:
        return "0:00"
    pace_sec = total_seconds / total_miles
    minutes = int(pace_sec // 60)
    seconds = int(pace_sec % 60)
    return f"{minutes}:{seconds:02d}"


def _fetch_from_api():
    if not SMASHRUN_TOKEN:
        return None

    # Monday of current week
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    from_ts = int(datetime.combine(monday, datetime.min.time()).timestamp())

    try:
        resp = requests.get(
            f"{API_BASE}/my/activities/search",
            params={"fromDateUTC": from_ts, "count": 50},
            headers={"Authorization": f"Bearer {SMASHRUN_TOKEN}"},
            timeout=10,
        )
        resp.raise_for_status()
        activities = resp.json()
    except Exception:
        return None

    daily = [0.0] * 7  # Mon-Sun
    total_miles = 0.0
    total_seconds = 0.0
    num_runs = 0

    for act in activities:
        distance_km = act.get("distance", 0)
        duration_sec = act.get("duration", 0)
        start_str = act.get("startDateTimeLocal", "")

        miles = distance_km * KM_TO_MILES
        total_miles += miles
        total_seconds += duration_sec
        num_runs += 1

        try:
            dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            day_idx = dt.weekday()
            daily[day_idx] += miles
        except (ValueError, AttributeError):
            pass

    daily = [round(d, 1) for d in daily]
    total_miles = round(total_miles, 1)

    return {
        "total_miles": total_miles,
        "num_runs": num_runs,
        "avg_pace": _format_pace(total_seconds, total_miles),
        "daily": daily,
    }


def get_weekly_data():
    global _cache, _cache_time

    now = time.time()
    if _cache and (now - _cache_time) < config.RUNNING_REFRESH:
        return _cache

    data = _fetch_from_api()
    if data is not None:
        _cache = data
        _cache_time = now
        return _cache

    if _cache is not None:
        return _cache
    return MOCK_DATA.copy()
