"""
tests/test_location_normalizer.py — Location normalizer tests (v0.3.1).

normalize_location() always returns a LocationResult — never raises.
_geocode_query is monkeypatched in every test so no real HTTP calls are made.

Covers:
  - successful normalization: name, coordinates, candidates, source
  - empty and whitespace-only query → error_code="empty_query"
  - no geocoding results → error_code="not_found", message includes query
  - multiple candidates: all returned, first is primary location
  - raw geocoding exception → error_code="geocoding_error", no raise
  - LocationResult and NormalizedLocation are importable Pydantic models
  - no real HTTP calls in any test
"""

import pytest

import luna.location.normalizer as normalizer_module
from luna.location.normalizer import normalize_location
from luna.location.schemas import LocationResult, NormalizedLocation


# ── Module-level async stubs ──────────────────────────────────────────────────

_PARIS_RAW = [
    {"name": "Paris", "latitude": 48.85, "longitude": 2.35,
     "country": "France", "country_code": "FR", "admin1": "Ile-de-France",
     "timezone": "Europe/Paris", "population": 2138551},
]

_MULTI_RAW = [
    {"name": "Springfield", "latitude": 39.80, "longitude": -89.64,
     "country": "United States", "country_code": "US", "admin1": "Illinois"},
    {"name": "Springfield", "latitude": 37.21, "longitude": -93.29,
     "country": "United States", "country_code": "US", "admin1": "Missouri"},
    {"name": "Springfield", "latitude": 42.10, "longitude": -72.59,
     "country": "United States", "country_code": "US", "admin1": "Massachusetts"},
]


async def _good_query(query):
    return _PARIS_RAW


async def _multi_query(query):
    return _MULTI_RAW


async def _empty_results(query):
    return []


async def _raise_query(query):
    raise Exception("Connection refused")


# ── Schema imports ────────────────────────────────────────────────────────────

def test_normalized_location_is_importable():
    assert NormalizedLocation is not None


def test_location_result_is_importable():
    assert LocationResult is not None


def test_normalized_location_can_be_constructed():
    loc = NormalizedLocation(query="Paris", name="Paris", latitude=48.85, longitude=2.35)
    assert loc.latitude == 48.85
    assert loc.source == "open_meteo_geocoding"


def test_location_result_can_be_constructed():
    result = LocationResult(success=False, error_code="not_found")
    assert result.success is False
    assert result.location is None
    assert result.candidates == []


# ── Success path ──────────────────────────────────────────────────────────────

async def test_success_returns_locationresult(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert isinstance(result, LocationResult)


async def test_success_flag_is_true(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.success is True


async def test_success_location_is_normalized_location(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert isinstance(result.location, NormalizedLocation)


async def test_success_location_name(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.name == "Paris"


async def test_success_location_latitude(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.latitude == 48.85


async def test_success_location_longitude(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.longitude == 2.35


async def test_success_location_country(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.country == "France"


async def test_success_location_country_code(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.country_code == "FR"


async def test_success_location_timezone(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.timezone == "Europe/Paris"


async def test_success_location_population(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.population == 2138551


async def test_success_location_source(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.source == "open_meteo_geocoding"


async def test_success_location_query_preserved(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.location.query == "Paris"


async def test_success_candidates_not_empty(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert len(result.candidates) >= 1


async def test_success_first_candidate_is_primary_location(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.candidates[0].name == result.location.name
    assert result.candidates[0].latitude == result.location.latitude


async def test_success_no_error_code(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("Paris")
    assert result.error_code is None


# ── Multiple candidates ───────────────────────────────────────────────────────

async def test_multiple_candidates_all_returned(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _multi_query)
    result = await normalize_location("Springfield")
    assert len(result.candidates) == 3


async def test_multiple_candidates_first_is_primary(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _multi_query)
    result = await normalize_location("Springfield")
    assert result.location.admin1 == "Illinois"


async def test_multiple_candidates_success_true(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _multi_query)
    result = await normalize_location("Springfield")
    assert result.success is True


# ── Empty query ───────────────────────────────────────────────────────────────

async def test_empty_query_returns_error(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("")
    assert result.success is False
    assert result.error_code == "empty_query"


async def test_whitespace_only_query_returns_error(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("   ")
    assert result.success is False
    assert result.error_code == "empty_query"


async def test_empty_query_location_is_none(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _good_query)
    result = await normalize_location("")
    assert result.location is None


# ── Not found ─────────────────────────────────────────────────────────────────

async def test_not_found_returns_error(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _empty_results)
    result = await normalize_location("Nonexistentia")
    assert result.success is False
    assert result.error_code == "not_found"


async def test_not_found_message_includes_query(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _empty_results)
    result = await normalize_location("Nonexistentia")
    assert "Nonexistentia" in result.error_message


async def test_not_found_location_is_none(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _empty_results)
    result = await normalize_location("Nonexistentia")
    assert result.location is None


async def test_not_found_candidates_empty(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _empty_results)
    result = await normalize_location("Nonexistentia")
    assert result.candidates == []


# ── Geocoding exception ───────────────────────────────────────────────────────

async def test_geocode_error_returns_locationresult(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _raise_query)
    result = await normalize_location("Paris")
    assert isinstance(result, LocationResult)


async def test_geocode_error_success_false(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _raise_query)
    result = await normalize_location("Paris")
    assert result.success is False


async def test_geocode_error_code(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _raise_query)
    result = await normalize_location("Paris")
    assert result.error_code == "geocoding_error"


async def test_geocode_error_message_set(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _raise_query)
    result = await normalize_location("Paris")
    assert result.error_message is not None
    assert len(result.error_message) > 0


async def test_geocode_error_location_is_none(monkeypatch):
    monkeypatch.setattr(normalizer_module, "_geocode_query", _raise_query)
    result = await normalize_location("Paris")
    assert result.location is None


# ── No real HTTP in any test ──────────────────────────────────────────────────

async def test_no_real_http_geocode_query_is_called(monkeypatch):
    """Confirm _geocode_query is invoked via monkeypatch, not real httpx."""
    called: list[str] = []

    async def _track(query):
        called.append(query)
        return _PARIS_RAW

    monkeypatch.setattr(normalizer_module, "_geocode_query", _track)
    await normalize_location("Paris")
    assert "Paris" in called
