"""
tests/test_weather_open_meteo.py — Open-Meteo weather provider tests (v0.3.0).

Covers:
  - mock provider still works via dispatcher (default config, no network)
  - open_meteo success: monkeypatched geocode + forecast → ToolResult.ok
  - open_meteo missing city → ToolResult.missing_args
  - geocode returns None (city not found) → ToolResult.error with helpful text
  - geocode raises → ToolResult.error, no raw exception escapes
  - forecast raises → ToolResult.error, no raw exception escapes
  - reply text contains city name and temperature
  - data dict has all expected keys
  - /simulate "weather in Rome" with mock provider end-to-end
  - no real HTTP: both network helpers are monkeypatched in all open_meteo tests
"""

import pytest
from httpx import ASGITransport, AsyncClient

import luna.config as config_module
import luna.tools.providers.weather_open_meteo as wom
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory
from luna.tools import dispatcher
from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus


# ── Module-level async stubs (no real HTTP) ───────────────────────────────────

async def _geo_paris(city):
    return (48.85, 2.35, "Paris")


async def _geo_rome(city):
    return (41.90, 12.50, "Rome")


async def _geo_london(city):
    return (51.51, -0.12, "London")


async def _geo_none(city):
    return None


async def _geo_raise(city):
    raise Exception("Simulated geocode failure")


async def _weather_ok(lat, lon):
    return {"current": {"temperature_2m": 18.5, "weather_code": 1, "wind_speed_10m": 12.0}}


async def _weather_cold(lat, lon):
    return {"current": {"temperature_2m": -3.0, "weather_code": 71, "wind_speed_10m": 5.0}}


async def _weather_raise(lat, lon):
    raise Exception("Simulated forecast failure")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


@pytest.fixture()
def use_open_meteo(monkeypatch):
    monkeypatch.setattr(config_module.settings, "weather_provider", "open_meteo")


@pytest.fixture()
def open_meteo_success(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_paris)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)


# ── Mock provider (default) still works ──────────────────────────────────────

async def test_mock_provider_returns_ok():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup",
        args={"city": "Rome"},
    ))
    assert result.status == ToolStatus.ok


async def test_mock_provider_reply_contains_city():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup",
        args={"city": "Rome"},
    ))
    assert "Rome" in result.reply_text


async def test_mock_provider_missing_city_returns_missing_args():
    result = await dispatcher.dispatch(ToolRequest(tool_name="weather_lookup"))
    assert result.status == ToolStatus.missing_args


# ── Open-Meteo success path ───────────────────────────────────────────────────

async def test_open_meteo_success_status(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert result.status == ToolStatus.ok


async def test_open_meteo_success_is_toolresult(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert isinstance(result, ToolResult)


async def test_open_meteo_reply_contains_city(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert "Paris" in result.reply_text


async def test_open_meteo_reply_contains_temperature(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert "18.5" in result.reply_text


async def test_open_meteo_reply_contains_wind(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert "12.0" in result.reply_text


async def test_open_meteo_data_has_all_expected_keys(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    for key in ("city", "latitude", "longitude", "temperature_c", "weather_code", "condition", "wind_speed_kmh"):
        assert key in result.data, f"Missing data key: {key}"


async def test_open_meteo_data_city_is_resolved_name(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert result.data["city"] == "Paris"


async def test_open_meteo_data_temperature_correct(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    assert result.data["temperature_c"] == 18.5


async def test_open_meteo_condition_label_set(open_meteo_success):
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Paris"},
    ))
    # weather_code=1 → "Mainly clear"
    assert result.data["condition"] == "Mainly clear"


async def test_open_meteo_snow_condition_label(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_rome)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_cold)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert result.data["condition"] == "Light snow"


# ── Missing city ──────────────────────────────────────────────────────────────

async def test_open_meteo_missing_city_returns_missing_args(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_paris)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    result = await dispatcher.dispatch(ToolRequest(tool_name="weather_lookup"))
    assert result.status == ToolStatus.missing_args


# ── Geocode not found ─────────────────────────────────────────────────────────

async def test_geocode_not_found_returns_error(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_none)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Nonexistentia"},
    ))
    assert result.status == ToolStatus.error


async def test_geocode_not_found_reply_names_the_city(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_none)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Nonexistentia"},
    ))
    assert "Nonexistentia" in result.reply_text


# ── Geocode raises ────────────────────────────────────────────────────────────

async def test_geocode_raises_returns_error(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_raise)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert result.status == ToolStatus.error


async def test_geocode_raises_no_raw_exception_escapes(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_raise)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    # Must return a ToolResult, not raise
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert isinstance(result, ToolResult)


async def test_geocode_raises_reply_is_user_friendly(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_raise)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_ok)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert "unavailable" in result.reply_text.lower()


# ── Forecast raises ───────────────────────────────────────────────────────────

async def test_forecast_raises_returns_error(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_rome)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_raise)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert result.status == ToolStatus.error


async def test_forecast_raises_no_raw_exception_escapes(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_rome)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_raise)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert isinstance(result, ToolResult)


async def test_forecast_raises_reply_is_user_friendly(use_open_meteo, monkeypatch):
    monkeypatch.setattr(wom, "_geocode_city", _geo_rome)
    monkeypatch.setattr(wom, "_fetch_current_weather", _weather_raise)
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "Rome"},
    ))
    assert "unavailable" in result.reply_text.lower()


# ── /simulate end-to-end (mock provider, no network) ─────────────────────────

async def test_simulate_weather_rome_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": "+447700900001",
            "body": "weather in Rome",
        })
    assert response.status_code == 200


async def test_simulate_weather_rome_reply_contains_rome():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": "+447700900001",
            "body": "weather in Rome",
        })
    assert "Rome" in response.json()["reply"]


# ── No real HTTP — monkeypatch covers all network helpers ─────────────────────

async def test_no_real_http_called(use_open_meteo, monkeypatch):
    """Verify both helpers are called via monkeypatch, not real httpx."""
    called: list[str] = []

    async def _track_geo(city):
        called.append("geo")
        return (51.51, -0.12, "London")

    async def _track_weather(lat, lon):
        called.append("weather")
        return {"current": {"temperature_2m": 15.0, "weather_code": 0, "wind_speed_10m": 8.0}}

    monkeypatch.setattr(wom, "_geocode_city", _track_geo)
    monkeypatch.setattr(wom, "_fetch_current_weather", _track_weather)

    await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup", args={"city": "London"},
    ))
    assert "geo" in called
    assert "weather" in called
