"""Mock flight_search — returns fixture data."""

from luna.tools.schemas import ToolRequest, ToolResult, ToolStatus


def run(request: ToolRequest) -> ToolResult:
    origin = request.args.get("origin", "")
    destination = request.args.get("destination", "")
    if not origin or not destination:
        return ToolResult(
            tool_name="flight_search",
            status=ToolStatus.missing_args,
            reply_text="What's your origin and destination city?",
        )
    return ToolResult(
        tool_name="flight_search",
        status=ToolStatus.ok,
        data={
            "origin": origin,
            "destination": destination,
            "results": [
                {"airline": "BA", "depart": "08:00", "price_gbp": 189},
                {"airline": "EZY", "depart": "13:30", "price_gbp": 124},
            ],
        },
        reply_text=(
            f"Flights {origin}→{destination}: "
            "BA 08:00 £189 · EZY 13:30 £124. "
            "Which would you like?"
        ),
    )
