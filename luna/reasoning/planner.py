"""
luna/reasoning/planner.py — Travel Planner.

Single public function: run(body, user_profile, active_tasks) → PlannerOutput.

Two implementations selected at runtime:
  1. Claude planner  — calls Claude API with tool use to get structured output.
                       Used when USE_CLAUDE_PLANNER=true AND ANTHROPIC_API_KEY is set.
  2. Fallback planner — deterministic keyword matching. Always available.
                        Used in all tests and local dev by default.

The fallback is not a toy. It covers the common travel intents and produces
actionable replies. It is the baseline that Claude replaces, not a stub.

No external API calls happen unless both flags are explicitly set.
"""

from luna.agent.schemas import PlannerOutput, RiskLevel, TaskPattern
from luna.config import settings

# ── System prompt (used by Claude planner only) ───────────────────────────────

_SYSTEM_PROMPT = """
You are Luna's travel planning engine. You receive an inbound SMS message from
a user and must produce a structured plan for how Luna should respond next.

Luna is an SMS-native agentic travel assistant. She helps users plan flights,
hotels, activities, and trips entirely through SMS. She never claims to have
booked something unless the system actually did it.

Task patterns:
- answer_with_context:          Answer directly from available information.
- ask_clarification:            Ask for missing information before acting.
- search_and_compare:           Search for options and present them (flights, hotels).
- monitor_and_alert:            Watch for a condition and notify (price drop, availability).
- booking_handoff:              Send a booking link to the user.
- modify_saved_trip:            Update an existing saved trip or itinerary.
- confirmation_required_action: An action is ready but requires explicit YES/NO.

Available tools: weather_lookup, events_search, flight_search, hotel_search,
maps_places, booking_handoff_link, ground_transport_stub, memory_search, memory_write.

Risk levels: low (information/search), medium (saves state), high (bookings).

Reply draft rules:
- Under 300 characters.
- Direct and helpful — no sycophantic openers.
- Never claim a booking is complete.
- Ask for exactly the missing fields you need — one question at a time.
- Never ask for passport or payment details.
""".strip()

# ── Public entry point ────────────────────────────────────────────────────────

def run(body: str, user_profile, active_tasks: list) -> PlannerOutput:
    """
    Produce a PlannerOutput for the current turn.

    Routes to Claude if USE_CLAUDE_PLANNER=true and ANTHROPIC_API_KEY is set.
    Falls back to the deterministic planner on any error or missing config.
    """
    if settings.use_claude_planner and settings.anthropic_api_key:
        try:
            return _run_claude(body, user_profile, active_tasks)
        except Exception:
            # Any Claude failure (network, validation, rate limit) → fallback
            return _run_fallback(body)
    return _run_fallback(body)


# ── Fallback planner ──────────────────────────────────────────────────────────

_WEATHER_KW  = ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny"]
_FLIGHT_KW   = ["flight", "fly", "plane", "airport", "airline", "depart", "arrive"]
_HOTEL_KW    = ["hotel", "stay", "accommodation", "hostel", "airbnb", "motel", "resort", "lodge"]
_EVENTS_KW   = ["event", "concert", "show", "restaurant", "reservation", "ticket", "festival", "tour", "activity"]


def _run_fallback(body: str) -> PlannerOutput:
    b = body.lower()

    if any(kw in b for kw in _WEATHER_KW):
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.answer_with_context,
            known_fields={},
            missing_fields=["city", "date"],
            candidate_tools=["weather_lookup"],
            selected_tools=[],
            risk_level=RiskLevel.low,
            next_action="ask_clarification",
            reply_draft="I can check travel weather for that. What city and date should I use?",
        )

    if any(kw in b for kw in _FLIGHT_KW):
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields={},
            missing_fields=["origin", "destination", "depart_date", "return_date", "passengers"],
            candidate_tools=["flight_search"],
            selected_tools=[],
            risk_level=RiskLevel.low,
            next_action="ask_clarification",
            reply_draft="I can help compare flights. What route and dates should I search?",
        )

    if any(kw in b for kw in _HOTEL_KW):
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields={},
            missing_fields=["city", "check_in", "check_out", "guests", "budget"],
            candidate_tools=["hotel_search"],
            selected_tools=[],
            risk_level=RiskLevel.low,
            next_action="ask_clarification",
            reply_draft="I can help compare hotels. What city, dates, and budget should I use?",
        )

    if any(kw in b for kw in _EVENTS_KW):
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields={},
            missing_fields=["city", "dates", "event_type"],
            candidate_tools=["events_search"],
            selected_tools=[],
            risk_level=RiskLevel.low,
            next_action="ask_clarification",
            reply_draft="I can help find travel events. Which city and dates should I check?",
        )

    # Unknown intent — ask what the user wants help with
    return PlannerOutput(
        goal=body,
        task_pattern=TaskPattern.ask_clarification,
        known_fields={},
        missing_fields=["travel_intent"],
        candidate_tools=[],
        selected_tools=[],
        risk_level=RiskLevel.low,
        next_action="ask_clarification",
        reply_draft="I'm Luna, your SMS-native travel assistant. Tell me what trip or place you want help with.",
    )


# ── Claude planner ────────────────────────────────────────────────────────────

# Tool schema passed to Claude to force structured output.
_PLANNER_TOOL = {
    "name": "plan_travel_action",
    "description": "Produce a structured plan for Luna's next action.",
    "input_schema": {
        "type": "object",
        "properties": {
            "goal":            {"type": "string", "description": "The user's travel goal in plain English."},
            "task_pattern":    {"type": "string", "enum": [p.value for p in TaskPattern]},
            "known_fields":    {"type": "object", "description": "Fields already collected from the user."},
            "missing_fields":  {"type": "array", "items": {"type": "string"}, "description": "Fields still needed."},
            "candidate_tools": {"type": "array", "items": {"type": "string"}, "description": "Tools that could fulfil this goal."},
            "selected_tools":  {"type": "array", "items": {"type": "string"}, "description": "Tools to call this turn (may be empty)."},
            "risk_level":      {"type": "string", "enum": ["low", "medium", "high"]},
            "next_action":     {"type": "string", "description": "What the runtime should do next."},
            "reply_draft":     {"type": "string", "description": "The SMS reply to send. Under 300 chars."},
        },
        "required": [
            "goal", "task_pattern", "known_fields", "missing_fields",
            "candidate_tools", "selected_tools", "risk_level", "next_action", "reply_draft",
        ],
    },
}


def _run_claude(body: str, user_profile, active_tasks: list) -> PlannerOutput:
    """
    Call Claude with tool use to produce a validated PlannerOutput.
    Raises on any error so the caller can fall back to _run_fallback.
    """
    import anthropic  # lazy import — only reached when USE_CLAUDE_PLANNER=true

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    active_task_summary = (
        f"Active tasks: {len(active_tasks)}. "
        + (f"Current goal: {active_tasks[-1].goal}" if active_tasks else "No active tasks.")
    )

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"[Context: {active_task_summary}]\n\nUser message: {body}",
            }
        ],
        tools=[_PLANNER_TOOL],
        tool_choice={"type": "any"},
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "plan_travel_action":
            return PlannerOutput(**block.input)

    # Claude responded without using the tool — treat as validation failure
    raise ValueError("Claude did not return a plan_travel_action tool call")
