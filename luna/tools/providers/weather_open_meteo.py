"""
luna/tools/providers/weather_open_meteo.py — Real weather via Open-Meteo.

Two module-level async helpers (_geocode_city, _fetch_current_weather) handle
all network I/O. They are kept separate from run() so tests can monkeypatch
them without touching httpx at all.

Open-Meteo is free, global, and requires no API key for basic use.
"""

import httpx

from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → human label.
# Unmapped codes fall back to "Variable conditions".
_WMO_LABELS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Freezing fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers", 81: "Showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm",
}


def _weather_label(code: int) -> str:
    return _WMO_LABELS.get(code, "Variable conditions")


async def _geocode_city(city: str) -> tuple[float, float, str] | None:
    """
    Return (latitude, longitude, resolved_name) for city, or None if not found.
    Raises httpx.HTTPStatusError / httpx.TransportError on network failure.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None
    r = results[0]
    return r["latitude"], r["longitude"], r.get("name", city)


async def _fetch_current_weather(lat: float, lon: float) -> dict:
    """
    Return the Open-Meteo current-weather JSON dict.
    Raises httpx.HTTPStatusError / httpx.TransportError on network failure.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
            },
        )
        response.raise_for_status()
    return response.json()


async def run(request: ToolRequest) -> ToolResult:
    """
    Open-Meteo weather lookup. Never raises — all errors are captured in
    a ToolResult with status=error so the agent runtime always gets a
    usable object.
    """
    city = request.args.get("city", "").strip()
    if not city:
        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.missing_args,
            reply_text="Which city should I check the weather for?",
        )

    try:
        geo = await _geocode_city(city)
        if geo is None:
            return ToolResult(
                tool_name="weather_lookup",
                status=ToolStatus.error,
                reply_text=(
                    f"I couldn't find weather data for '{city}'. "
                    "Try a more specific city name."
                ),
            )
        lat, lon, resolved_name = geo

        weather_data = await _fetch_current_weather(lat, lon)
        current = weather_data["current"]
        temp = current["temperature_2m"]
        code = current["weather_code"]
        wind = current["wind_speed_10m"]
        label = _weather_label(code)

        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.ok,
            data={
                "city": resolved_name,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": temp,
                "weather_code": code,
                "condition": label,
                "wind_speed_kmh": wind,
            },
            reply_text=f"{resolved_name}: {label}, {temp}°C, wind {wind} km/h.",
        )
    except Exception as exc:
        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.error,
            reply_text="Weather data is temporarily unavailable. Please try again shortly.",
            data={"error": str(exc)},
        )
