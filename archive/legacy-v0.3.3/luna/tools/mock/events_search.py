"""Mock events_search — returns fixture data."""

from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus


def run(request: ToolRequest) -> ToolResult:
    city = request.args.get("city", "")
    if not city:
        return ToolResult(
            tool_name="events_search",
            status=ToolStatus.missing_args,
            reply_text="Which city should I search for events?",
        )
    return ToolResult(
        tool_name="events_search",
        status=ToolStatus.ok,
        data={
            "city": city,
            "results": [
                {"name": "Jazz Night", "venue": "The Blue Note", "date": "Fri 8pm"},
                {"name": "Food Festival", "venue": "City Park", "date": "Sat–Sun"},
            ],
        },
        reply_text=(
            f"Events in {city}: "
            "Jazz Night @ The Blue Note Fri 8pm · Food Festival @ City Park Sat–Sun. "
            "Interested in either?"
        ),
    )
