"""
Weather lookup tool (e.g. via OpenWeatherMap or WeatherAPI.com — pick
one and set WEATHER_API_KEY in .env accordingly).

Owner: Rabia

This is the template for any future tool: one function, plain string
return, registered in tools/tool_registry.py.
"""

import requests

from config import WEATHER_API_KEY


def get_weather(city: str) -> str:
    """
    TODO(Rabia): call the weather API for `city` and return a short
    human-readable string, e.g. "Lahore: 34°C, sunny."
    Handle the "city not found" / API error case and return a plain
    string explaining it (don't raise — this return value goes straight
    back to Gemini as the tool result).
    """
    raise NotImplementedError("Rabia: implement weather lookup")
