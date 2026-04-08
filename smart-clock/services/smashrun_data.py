"""
SmashRun data provider.

Currently returns mock data. To integrate with the real SmashRun API:
1. Register an app at https://smashrun.com/developers
2. Obtain an OAuth2 access token
3. Replace get_weekly_data() with a real API call to:
   GET https://api.smashrun.com/v1/my/activities/search
   Headers: Authorization: Bearer <YOUR_TOKEN>
4. Parse the response to compute weekly totals.
"""

import time
import config

_cache = None
_cache_time = 0

# Mock data for development
MOCK_DATA = {
    "total_miles": 12.4,
    "num_runs": 3,
    "avg_pace": "8:42",
    "daily": [3.1, 0.0, 5.2, 0.0, 4.1, 0.0, 0.0],  # Mon-Sun
}


def get_weekly_data():
    global _cache, _cache_time

    now = time.time()
    if _cache and (now - _cache_time) < config.RUNNING_REFRESH:
        return _cache

    # TODO: Replace with real SmashRun API call
    _cache = MOCK_DATA.copy()
    _cache_time = now
    return _cache
