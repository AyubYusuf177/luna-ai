"""
luna/tools/dispatcher.py — Routes a ToolRequest to its implementation.

Never raises. Returns a ToolResult with status=error or status=disabled
when something goes wrong, so the runtime always gets a usable object.

dispatch() is async so that provider implementations can use async HTTP
(e.g. the Open-Meteo weather provider). Sync mock implementations are
called directly; async implementations are awaited.
"""

import asyncio
import importlib

from luna.config import settings
from luna.tools import registry
from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus

# Cache for mock tool implementations (lazy-loaded by convention).
# weather_lookup is deliberately excluded — it is routed per-request
# based on settings.weather_provider so tests can switch providers.
_IMPLEMENTATIONS: dict[str, object] = {}


def _get_impl(name: str):
    # weather_lookup: provider-aware routing, not cached.
    if name == "weather_lookup":
        if settings.weather_provider == "open_meteo":
            from luna.tools.providers import weather_open_meteo
            return weather_open_meteo.run
        from luna.tools.mock import weather_lookup as _mock_weather
        return _mock_weather.run

    if name in _IMPLEMENTATIONS:
        return _IMPLEMENTATIONS[name]
    try:
        mod = importlib.import_module(f"luna.tools.mock.{name}")
        _IMPLEMENTATIONS[name] = mod.run
        return mod.run
    except ModuleNotFoundError:
        return None


async def dispatch(request: ToolRequest) -> ToolResult:
    """Route a ToolRequest to its implementation and return a ToolResult."""
    definition = registry.get(request.tool_name)

    if definition is None:
        return ToolResult(
            tool_name=request.tool_name,
            status=ToolStatus.error,
            reply_text=f"Tool '{request.tool_name}' is not registered.",
        )

    if not definition.enabled_in_v0:
        return ToolResult(
            tool_name=request.tool_name,
            status=ToolStatus.disabled,
            reply_text=f"Tool '{request.tool_name}' is not available yet.",
        )

    impl = _get_impl(request.tool_name)
    if impl is None:
        return ToolResult(
            tool_name=request.tool_name,
            status=ToolStatus.error,
            reply_text=f"Tool '{request.tool_name}' has no implementation.",
        )

    try:
        if asyncio.iscoroutinefunction(impl):
            return await impl(request)
        return impl(request)
    except Exception as exc:
        return ToolResult(
            tool_name=request.tool_name,
            status=ToolStatus.error,
            reply_text="I ran into a problem checking that. Let me try a different approach.",
            data={"error": str(exc)},
        )
