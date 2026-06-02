"""Mock hotel_search — returns fixture data."""

from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus


def run(request: ToolRequest) -> ToolResult:
    city = request.args.get("city", "")
    if not city:
        return ToolResult(
            tool_name="hotel_search",
            status=ToolStatus.missing_args,
            reply_text="Which city should I search hotels in?",
        )
    return ToolResult(
        tool_name="hotel_search",
        status=ToolStatus.ok,
        data={
            "city": city,
            "results": [
                {"name": "City Central Hotel", "stars": 4, "price_gbp_night": 110},
                {"name": "Budget Inn", "stars": 3, "price_gbp_night": 65},
            ],
        },
        reply_text=(
            f"Hotels in {city}: "
            "City Central ★★★★ £110/night · Budget Inn ★★★ £65/night. "
            "Want more details?"
        ),
    )
