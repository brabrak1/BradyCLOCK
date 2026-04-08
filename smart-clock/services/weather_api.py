import time
import requests
import config

WEATHER_CODES = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Foggy",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
    99: "Severe thunderstorm",
}

RAIN_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}

_cache = None
_cache_time = 0


def is_rainy(code):
    return code in RAIN_CODES


def get_condition_text(code):
    return WEATHER_CODES.get(code, "Unknown")


def get_condition_symbol(code):
    if code == 0:
        return "\u2600"
    if code in (1, 2, 3):
        return "\u26c5"
    if code in (45, 48):
        return "\u2601"
    if code in RAIN_CODES:
        return "\u2602"
    if code in (71, 73, 75, 77, 85, 86):
        return "\u2744"
    return "\u2601"


def get_clothing_advice(temp, code):
    prefix = "Bring an umbrella! " if is_rainy(code) else ""
    if temp < 40:
        return prefix + "Bundle up! Heavy coat, gloves, and a warm hat."
    elif temp < 55:
        return prefix + "Grab a jacket and maybe a scarf."
    elif temp < 65:
        return prefix + "A light jacket or sweater should do."
    elif temp < 75:
        return prefix + "Light layers and sunglasses today!"
    elif temp < 85:
        return prefix + "Shorts and sunscreen weather!"
    else:
        return prefix + "Stay cool \u2014 light clothes, lots of water."


def fetch_weather():
    global _cache, _cache_time

    now = time.time()
    if _cache and (now - _cache_time) < config.WEATHER_REFRESH:
        return _cache

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={config.LAT}&longitude={config.LON}"
        f"&current=temperature_2m,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&temperature_unit=fahrenheit"
        f"&timezone={config.TIMEZONE}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current"]
        daily = data["daily"]
        hourly = data["hourly"]

        # Find the next 6 hours from now
        from datetime import datetime
        now_dt = datetime.now()
        hourly_times = hourly["time"]
        hourly_temps = hourly["temperature_2m"]
        hourly_codes = hourly["weather_code"]

        upcoming = []
        for i, t_str in enumerate(hourly_times):
            hr_dt = datetime.fromisoformat(t_str)
            if hr_dt > now_dt and len(upcoming) < 6:
                upcoming.append({
                    "hour": hr_dt.strftime("%-I%p").lower(),
                    "temp": round(hourly_temps[i]),
                    "code": hourly_codes[i],
                })

        result = {
            "temp": round(current["temperature_2m"]),
            "code": current["weather_code"],
            "wind": round(current["wind_speed_10m"]),
            "high": round(daily["temperature_2m_max"][0]),
            "low": round(daily["temperature_2m_min"][0]),
            "hourly": upcoming,
            "offline": False,
        }

        _cache = result
        _cache_time = now
        return result

    except Exception:
        if _cache:
            return {**_cache, "offline": True}
        return {
            "temp": 0,
            "code": 0,
            "wind": 0,
            "high": 0,
            "low": 0,
            "hourly": [],
            "offline": True,
        }
