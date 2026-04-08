"""
Google Calendar data provider.
Uses real Google Calendar API with OAuth2 credentials.
Falls back to mock data if no token.json exists yet.
Run auth_calendar.py once to generate the token.
"""

import os
import time
from datetime import datetime, timedelta

import config

_cache = None
_cache_time = 0

# Keywords for auto-categorizing events
FOOD_KEYWORDS = {"lunch", "dinner", "breakfast", "coffee", "eat", "brunch", "meal", "food"}
EXERCISE_KEYWORDS = {"run", "gym", "workout", "swim", "bike", "hike", "yoga", "exercise", "walk", "lift"}

MOCK_EVENTS = [
    {"time": "9:00 AM", "title": "Team standup", "category": "default"},
    {"time": "11:30 AM", "title": "Lunch with Alex", "category": "food"},
    {"time": "2:00 PM", "title": "Design review", "category": "default"},
    {"time": "5:30 PM", "title": "Run (5mi planned)", "category": "exercise"},
]


def _categorize(title):
    lower = title.lower()
    for kw in FOOD_KEYWORDS:
        if kw in lower:
            return "food"
    for kw in EXERCISE_KEYWORDS:
        if kw in lower:
            return "exercise"
    return "default"


def _get_calendar_service():
    """Build and return an authorized Google Calendar API service."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return None

    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config.CALENDAR_TOKEN)

    if not os.path.exists(token_path):
        return None

    creds = Credentials.from_authorized_user_file(token_path, config.CALENDAR_SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        except Exception:
            return None

    if not creds.valid:
        return None

    return build("calendar", "v3", credentials=creds)


def _fetch_from_api():
    """Fetch today's events from Google Calendar API."""
    service = _get_calendar_service()
    if service is None:
        return None

    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    time_min = start_of_day.astimezone().isoformat()
    time_max = end_of_day.astimezone().isoformat()

    result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=10,
    ).execute()

    events = []
    for item in result.get("items", []):
        start = item.get("start", {})
        title = item.get("summary", "(No title)")

        # Parse start time
        if "dateTime" in start:
            dt = datetime.fromisoformat(start["dateTime"])
            time_str = dt.strftime("%-I:%M %p")
        elif "date" in start:
            time_str = "All day"
        else:
            continue

        events.append({
            "time": time_str,
            "title": title,
            "category": _categorize(title),
        })

    return events


def get_todays_events():
    global _cache, _cache_time

    now = time.time()
    if _cache is not None and (now - _cache_time) < config.CALENDAR_REFRESH:
        return _cache

    events = _fetch_from_api()
    if events is not None:
        _cache = events
        _cache_time = now
        return _cache

    # API unavailable — use cached or mock fallback
    if _cache is not None:
        return _cache
    return list(MOCK_EVENTS)
