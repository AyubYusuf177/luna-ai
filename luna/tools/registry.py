"""
luna/tools/registry.py — Named registry of ToolDefinition objects.

All tools registered here are available to the dispatcher.
is_mock=True tools return fixture data (safe for tests and local dev).
"""

from luna.agent.schemas import RiskLevel
from luna.tools.schemas import ToolDefinition

_registry: dict[str, ToolDefinition] = {}


def register(tool: ToolDefinition) -> None:
    _registry[tool.name] = tool


def get(name: str) -> ToolDefinition | None:
    return _registry.get(name)


def all_tools() -> list[ToolDefinition]:
    return list(_registry.values())


# ── Register the v0.0.5 mock tools ───────────────────────────────────────────

register(ToolDefinition(
    name="weather_lookup",
    description="Returns current weather and forecast for a city.",
    risk_level=RiskLevel.low,
    is_mock=True,
    enabled_in_v0=True,
))

register(ToolDefinition(
    name="flight_search",
    description="Searches for available flights between two cities.",
    risk_level=RiskLevel.low,
    is_mock=True,
    enabled_in_v0=True,
))

register(ToolDefinition(
    name="hotel_search",
    description="Searches for hotels in a city for given dates.",
    risk_level=RiskLevel.low,
    is_mock=True,
    enabled_in_v0=True,
))

register(ToolDefinition(
    name="events_search",
    description="Searches for events, concerts, and restaurants in a city.",
    risk_level=RiskLevel.low,
    is_mock=True,
    enabled_in_v0=True,
))
