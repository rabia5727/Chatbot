"""Example tool: current weather lookup via Open-Meteo (no API key required).

Registered into tools.tool_registry so Gemini can call it via function
calling. Kept deliberately simple -- this is a demo tool, swap for a paid
provider later if needed.
"""

from __future__ import annotations

import requests

from tools.tool_registry import register

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_SECONDS = 10


@register(
    name="get_weather",
    description="Get the current weather (temperature, windspeed) for a given city name.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'Lahore' or 'London'.",
            }
        },
        "required": ["city"],
    },
)
def get_weather(city: str) -> dict:
    """Look up a city and return its current weather conditions."""
    geo_response = requests.get(
        _GEOCODE_URL, params={"name": city, "count": 1}, timeout=_TIMEOUT_SECONDS
    )
    geo_response.raise_for_status()
    results = geo_response.json().get("results")
    if not results:
        raise ValueError(f"Could not find a location matching '{city}'.")

    location = results[0]
    forecast_response = requests.get(
        _FORECAST_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current_weather": True,
        },
        timeout=_TIMEOUT_SECONDS,
    )
    forecast_response.raise_for_status()
    current = forecast_response.json().get("current_weather", {})

    return {
        "city": location.get("name"),
        "country": location.get("country"),
        "temperature_c": current.get("temperature"),
        "windspeed_kmh": current.get("windspeed"),
    }
