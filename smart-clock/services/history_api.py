import time
import requests
from datetime import date

import config

_cache = None
_cache_date = None


def fetch_history():
    global _cache, _cache_date

    today = date.today()
    if _cache and _cache_date == today:
        return _cache

    month = today.month
    day = today.day
    url = (
        f"https://api.wikimedia.org/feed/v1/wikipedia/en"
        f"/onthisday/selected/{month}/{day}"
    )

    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "BradyClock/1.0"
        })
        resp.raise_for_status()
        data = resp.json()

        events = data.get("selected", [])
        # Pick 3 events spread across eras
        picked = _pick_diverse_events(events, 3)

        result = {
            "date_label": today.strftime("%B %-d"),
            "events": picked,
            "offline": False,
        }

        _cache = result
        _cache_date = today
        return result

    except Exception:
        if _cache:
            return {**_cache, "offline": True}
        return {
            "date_label": today.strftime("%B %-d"),
            "events": [],
            "offline": True,
        }


def _pick_diverse_events(events, count):
    if len(events) <= count:
        return [_format_event(e) for e in events]

    # Sort by year, pick evenly spaced
    sorted_events = sorted(events, key=lambda e: e.get("year", 0))
    step = len(sorted_events) / count
    picked = []
    for i in range(count):
        idx = int(i * step)
        picked.append(_format_event(sorted_events[idx]))
    return picked


def _format_event(event):
    year = event.get("year", "")
    text = event.get("text", "")
    # Truncate long descriptions
    if len(text) > 120:
        text = text[:117] + "..."
    return {"year": str(year), "text": text}
