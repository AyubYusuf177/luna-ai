"""
luna/location/normalizer.py — Shared location normalization.

normalize_location(query) turns a free-text location string into a
structured NormalizedLocation. Currently backed by Open-Meteo geocoding
(free, no API key). Never raises — all errors are returned as a
LocationResult with success=False.

_geocode_query is module-level so tests can monkeypatch it without
touching httpx. Same pattern as _call_claude_once in the planner.
"""

import httpx

from luna.location.schemas import LocationResult, NormalizedLocation

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


async def _geocode_query(query: str) -> list[dict]:
    """
    Call Open-Meteo geocoding and return the raw results list.
    Returns [] if no matches. Raises on network / HTTP failure.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _GEOCODE_URL,
            params={"name": query, "count": 5, "language": "en", "format": "json"},
        )
        response.raise_for_status()
    return response.json().get("results") or []


async def normalize_location(query: str) -> LocationResult:
    """
    Normalize a free-text location string into a structured LocationResult.

    Always returns a LocationResult — never raises.

    Error codes:
      "empty_query"      — blank or whitespace-only input
      "not_found"        — geocoder returned no results
      "geocoding_error"  — network or HTTP failure
    """
    query = query.strip()
    if not query:
        return LocationResult(
            success=False,
            error_code="empty_query",
            error_message="Location query cannot be empty.",
        )

    try:
        raw = await _geocode_query(query)
    except Exception as exc:
        return LocationResult(
            success=False,
            error_code="geocoding_error",
            error_message=str(exc),
        )

    if not raw:
        return LocationResult(
            success=False,
            error_code="not_found",
            error_message=f"No location found for '{query}'.",
        )

    candidates = [
        NormalizedLocation(
            query=query,
            name=r.get("name", query),
            country=r.get("country"),
            country_code=r.get("country_code"),
            admin1=r.get("admin1"),
            latitude=r["latitude"],
            longitude=r["longitude"],
            timezone=r.get("timezone"),
            population=r.get("population"),
        )
        for r in raw
    ]

    return LocationResult(
        success=True,
        location=candidates[0],
        candidates=candidates,
    )
