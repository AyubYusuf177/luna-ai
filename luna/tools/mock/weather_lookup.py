"""Mock weather_lookup — returns fixture data."""

from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus


def run(request: ToolRequest) -> ToolResult:
    city = request.args.get("city", "")
    if not city:
        return ToolResult(
            tool_name="weather_lookup",
            status=ToolStatus.missing_args,
            reply_text="Which city should I check the weather for?",
        )
    return ToolResult(
        tool_name="weather_lookup",
        status=ToolStatus.ok,
        data={"city": city, "condition": "Sunny", "high_c": 24, "low_c": 14},
        reply_text=f"{city}: Sunny, high 24°C / low 14°C. Good travel weather.",
    )
