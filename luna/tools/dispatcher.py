"""
luna/tools/dispatcher.py — Routes a ToolRequest to its implementation.

Never raises. Returns a ToolResult with status=error or status=disabled
when something goes wrong, so the runtime always gets a usable object.
"""

from luna.tools import registry
from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus

# Map of registered tool names to their run() callables.
_IMPLEMENTATIONS: dict[str, object] = {}


def _get_impl(name: str):
    if name in _IMPLEMENTATIONS:
        return _IMPLEMENTATIONS[name]
    # Lazy-load mock implementations by convention.
    try:
        import importlib
        mod = importlib.import_module(f"luna.tools.mock.{name}")
        _IMPLEMENTATIONS[name] = mod.run
        return mod.run
    except ModuleNotFoundError:
        return None


def dispatch(request: ToolRequest) -> ToolResult:
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
        return impl(request)
    except Exception as exc:
        return ToolResult(
            tool_name=request.tool_name,
            status=ToolStatus.error,
            reply_text="I ran into a problem checking that. Let me try a different approach.",
            data={"error": str(exc)},
        )
