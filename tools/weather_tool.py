"""
Weather lookup tool, using OpenWeatherMap's Current Weather API.
Get a free API key at https://openweathermap.org/api and set
WEATHER_API_KEY in .env.

Owner: Rabia

This is the template for any future tool: one function, plain string
return, registered in tools/tool_registry.py.
"""

import requests

from config import WEATHER_API_KEY

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str) -> str:
    """
    Return a short human-readable weather summary for `city`, e.g.
    "Lahore: 34°C, clear sky." Never raises — errors come back as a
    plain string so Gemini can relay them to the user.
    """
    if not WEATHER_API_KEY:
        return "Weather lookup isn't configured (missing WEATHER_API_KEY)."

    try:
        response = requests.get(
            BASE_URL,
            params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"},
            timeout=5,
        )
    except requests.RequestException:
        return f"Couldn't reach the weather service for {city} right now."

    if response.status_code == 404:
        return f"Couldn't find a city called '{city}'."
    if response.status_code != 200:
        return f"Weather lookup for {city} failed ({response.status_code})."

    data = response.json()
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    return f"{city}: {temp:.0f}°C, {description}."
