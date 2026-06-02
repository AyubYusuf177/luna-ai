"""
luna/location/schemas.py — Shared location data contracts.

NormalizedLocation: structured output from any geocoding provider.
LocationResult: the envelope normalize_location() always returns.
"""

from __future__ import annotations

from pydantic import BaseModel


class NormalizedLocation(BaseModel):
    query: str                        # original user string
    name: str                         # resolved display name
    country: str | None = None
    country_code: str | None = None   # ISO 3166-1 alpha-2
    admin1: str | None = None         # state / region
    latitude: float
    longitude: float
    timezone: str | None = None
    population: int | None = None
    confidence: float | None = None   # reserved; not set in v0.3.1
    source: str = "open_meteo_geocoding"


class LocationResult(BaseModel):
    success: bool
    location: NormalizedLocation | None = None
    candidates: list[NormalizedLocation] = []
    error_code: str | None = None     # "empty_query" | "not_found" | "geocoding_error"
    error_message: str | None = None
