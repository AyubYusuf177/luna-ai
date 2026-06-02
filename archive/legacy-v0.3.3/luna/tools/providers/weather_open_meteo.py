"""
luna/tools/providers/weather_open_meteo.py — Real weather via Open-Meteo.

Location resolution is delegated to luna.location.normalizer so that all
tools share a single geocoding path. This provider owns only the
weather-specific forecast call (_fetch_current_weather).

_fetch_current_weather is module-level so tests can monkeypatch it without
touching httpx. Geocoding is patched via normalizer._geocode_query.
"""

import httpx

from luna.location.normalizer import normalize_location
from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → human label.
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
        loc_result = await normalize_location(city)
        if not loc_result.success:
            if loc_result.error_code == "not_found":
                reply_text = (
                    f"I couldn't find weather data for '{city}'. "
                    "Try a more specific city name."
                )
            else:
                reply_text = (
                    "Weather data is temporarily unavailable. "
                    "Please try again shortly."
                )
            return ToolResult(
                tool_name="weather_lookup",
                status=ToolStatus.error,
                reply_text=reply_text,
            )

        loc = loc_result.location
        weather_data = await _fetch_current_weather(loc.latitude, loc.longitude)
        current = weather_data["current"]
        temp = current["temperature_2m"]
        code = current["weather_code"]
        wind = current["wind_speed_10m"]
        label = _weather_label(code)

        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.ok,
            data={
                "city": loc.name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "temperature_c": temp,
                "weather_code": code,
                "condition": label,
                "wind_speed_kmh": wind,
            },
            reply_text=f"{loc.name}: {label}, {temp}°C, wind {wind} km/h.",
        )
    except Exception as exc:
        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.error,
            reply_text="Weather data is temporarily unavailable. Please try again shortly.",
            data={"error": str(exc)},
        )
