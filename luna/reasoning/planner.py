"""
luna/reasoning/planner.py — Travel Planner (v0.2.2).

Single public function: run(body, user_profile, active_tasks) → PlannerOutput.

Two implementations selected at runtime:
  1. Claude planner  — Calls Claude with tool-use to get a validated PlannerOutput.
                       Used when USE_CLAUDE_PLANNER=true AND ANTHROPIC_API_KEY is set.
                       Retries once with a stricter repair prompt on validation failure.
                       Falls back to the deterministic planner if both attempts fail.
  2. Fallback planner — Deterministic keyword + regex matching. Always available.
                        Used in all tests and local dev by default.

Design notes:
  - _call_claude_once(client, messages) → (raw_dict, usage | None).
    Module-level so tests can patch it: monkeypatch.setattr(
        "luna.reasoning.planner._call_claude_once", lambda client, msgs: (raw, None))
  - _run_claude() takes a mutable td dict so retry_count is captured even when
    the second attempt raises and run() catches the exception.
  - run() emits a planner_run event after every call (fallback or Claude) with
    safe, non-sensitive metadata for observability.
  - No real API call happens unless both USE_CLAUDE_PLANNER and ANTHROPIC_API_KEY
    are set.
"""

import re
import time
from dataclasses import dataclass, field

from luna.agent.schemas import PlannerOutput, RiskLevel, TaskPattern
from luna.config import settings

# ── Planner trace ─────────────────────────────────────────────────────────────

@dataclass
class PlannerTrace:
    """Lightweight record of a single planner invocation. Logged as event metadata."""
    planner_mode: str                    # "fallback" | "claude"
    used_claude: bool
    fallback_used: bool
    retry_count: int
    latency_ms: float
    selected_tools: list = field(default_factory=list)
    model: str | None = None
    fallback_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    task_pattern: str | None = None
    validation_error: str | None = None


# ── Cost estimator ────────────────────────────────────────────────────────────

# USD per million tokens. Update when Anthropic changes pricing.
_COST_PER_MTOK: dict[str, tuple[float, float]] = {
    # model_id: (input_usd_per_mtok, output_usd_per_mtok)
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80,  4.00),
    "claude-opus-4-7":           (15.00, 75.00),
}


def _estimate_cost(
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    """Return estimated USD cost or None if any input is absent/unknown."""
    if model is None or input_tokens is None or output_tokens is None:
        return None
    rates = _COST_PER_MTOK.get(model)
    if rates is None:
        return None
    input_rate, output_rate = rates
    return round(
        (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000, 8
    )

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are Luna's travel planning engine. You receive an inbound SMS message from a
user and must call the plan_travel_action tool with a structured plan.

== LUNA'S IDENTITY ==
Luna is an SMS-native agentic travel OPERATOR — not a chatbot, not a workflow
wizard. She understands flexible, ambiguous, real-world travel requests and turns
them into actionable plans. She works in the travel domain only.

== YOUR JOB ==
Analyse the user's message (and any active-task context provided). Then call
plan_travel_action with all required fields.

goal            — The user's travel goal restated in one clear sentence.
task_pattern    — The most appropriate pattern (see list below).
known_fields    — Every field you can extract from the message or context.
                  Extract as much as possible: cities, dates, budgets, duration,
                  passenger counts, preferences, constraints, exclusions.
missing_fields  — Fields you still need before you can act. List only the ones
                  you actually need for the selected tool or next action.
candidate_tools — All tools relevant to this goal (may be more than one).
selected_tools  — Only tools you can call RIGHT NOW because required args exist.
                  Empty if any required arg is missing.
risk_level      — low (search/info), medium (saves state), high (booking action).
next_action     — One of: execute_tool | ask_clarification | create_confirmation | send_reply
reply_draft     — The SMS reply. Under 280 characters. No greetings or openers.
                  Direct, helpful, specific. Ask for ONE missing field at a time.

== TASK PATTERNS ==
answer_with_context          Use when you can answer directly (weather for a known city,
                             simple factual questions about travel).
ask_clarification            A required field is missing. Ask for exactly one field.
search_and_compare           Find and surface options: flights, hotels, events.
monitor_and_alert            Watch for a condition and notify: price drop, availability.
booking_handoff              User is ready to book — send a secure booking link.
modify_saved_trip            Update an existing saved trip or itinerary.
confirmation_required_action Action is ready but needs explicit YES/NO (medium/high risk).

== AVAILABLE TOOLS AND THEIR REQUIRED ARGS ==
weather_lookup   — REQUIRED: city
flight_search    — REQUIRED: origin AND destination
hotel_search     — REQUIRED: city
events_search    — REQUIRED: city

Only include a tool in selected_tools if ALL its required args are in known_fields.

== INTERPRETING MESSY REQUESTS ==
Real travel messages are ambiguous. Extract everything you can:
- "somewhere warm in June under £500 not Spain" →
    known_fields: {month: "June", budget_max: 500, climate: "warm",
                   excluded_destinations: ["Spain"]}
    missing_fields: ["origin", "destination"] (ask for origin first)
- "I land in Rome at 9pm, need a hotel near the station and something relaxed
  to do in the morning" →
    known_fields: {destination: "Rome", arrival_time: "21:00",
                   hotel_preference: "near station",
                   activity_preference: "relaxed morning activity"}
    candidate_tools: [hotel_search, events_search]
    selected_tools: [hotel_search]  (city known)
- "Keep an eye on Tokyo for October, only tell me if meaningfully cheaper" →
    task_pattern: monitor_and_alert
    known_fields: {destination: "Tokyo", date_window: "October",
                   alert_condition: "meaningfully cheaper than usual"}
    missing_fields: ["origin"]
- "Book me an Uber from my hotel to the airport at 6am tomorrow" →
    task_pattern: confirmation_required_action
    risk_level: medium
    known_fields: {pickup: "hotel", destination: "airport", time: "06:00",
                   date: "tomorrow"}
    reply_draft must NOT claim the ride is booked.

== ACTIVE TASK CONTEXT ==
If context shows a prior task, merge new information into known_fields.
Do not discard previously extracted fields.

== POLICY CONSTRAINTS ==
- Never ask for passport number, national ID, card number, CVV, or IBAN.
- Never claim a booking is complete unless a booking event was confirmed.
- risk_level medium or high → use confirmation_required_action unless confirmed.
- reply_draft must be under 280 characters, SMS-appropriate, no emojis.
- Travel domain only. For off-topic messages use ask_clarification.
""".strip()

# ── Tool schema passed to Claude ───────────────────────────────────────────────

_PLANNER_TOOL = {
    "name": "plan_travel_action",
    "description": "Produce a structured plan for Luna's next action based on the user's SMS.",
    "input_schema": {
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "description": "The user's travel goal in one clear sentence.",
            },
            "task_pattern": {
                "type": "string",
                "enum": [p.value for p in TaskPattern],
                "description": "How Luna should handle this goal.",
            },
            "known_fields": {
                "type": "object",
                "description": "All fields extracted from the message and context.",
            },
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Fields still needed. Ask for one at a time.",
            },
            "candidate_tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "All tools relevant to this goal.",
            },
            "selected_tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tools to call this turn (required args present). May be empty.",
            },
            "risk_level": {
                "type": "string",
                "enum": ["low", "medium", "high"],
            },
            "next_action": {
                "type": "string",
                "description": "execute_tool | ask_clarification | create_confirmation | send_reply",
            },
            "reply_draft": {
                "type": "string",
                "description": "SMS reply to send. Under 280 chars. No openers.",
            },
        },
        "required": [
            "goal", "task_pattern", "known_fields", "missing_fields",
            "candidate_tools", "selected_tools", "risk_level",
            "next_action", "reply_draft",
        ],
    },
}


# ── Public entry point ────────────────────────────────────────────────────────

def run(body: str, user_profile, active_tasks: list) -> PlannerOutput:
    """
    Produce a PlannerOutput for the current turn.

    Routes to Claude if USE_CLAUDE_PLANNER=true and ANTHROPIC_API_KEY is set.
    Falls back to the deterministic planner on any error or missing config.

    Always emits a planner_run event with non-sensitive trace metadata.
    Also emits planner_fallback_used (legacy) when Claude fails, for backwards
    compatibility with existing event-log consumers.
    """
    from luna.events import logger as events

    uid = getattr(user_profile, "user_id", "system")
    t0 = time.monotonic()

    # Mutable trace data — _run_claude populates it even if it raises.
    td: dict = {
        "retry_count": 0,
        "input_tokens": None,
        "output_tokens": None,
        "validation_error": None,
    }
    planner_mode = "fallback"
    used_claude = False
    fallback_used = False
    fallback_reason: str | None = None

    if settings.use_claude_planner and settings.anthropic_api_key:
        try:
            result = _run_claude(body, user_profile, active_tasks, td)
            planner_mode = "claude"
            used_claude = True
        except Exception:
            fallback_used = True
            fallback_reason = "claude_planner_failed"
            events.log("planner_fallback_used", uid, {"reason": "claude_planner_failed"})
            result = _run_fallback(body)
    else:
        result = _run_fallback(body)

    latency_ms = round((time.monotonic() - t0) * 1000, 1)
    model = settings.anthropic_model if used_claude else None

    events.log("planner_run", uid, {
        "planner_mode": planner_mode,
        "model": model,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "retry_count": td["retry_count"],
        "latency_ms": latency_ms,
        "input_tokens": td["input_tokens"],
        "output_tokens": td["output_tokens"],
        "estimated_cost_usd": _estimate_cost(model, td["input_tokens"], td["output_tokens"]),
        "task_pattern": result.task_pattern.value,
        "selected_tools": list(result.selected_tools),
    })

    return result


# ── Claude planner ────────────────────────────────────────────────────────────

def _build_context(active_tasks: list) -> str:
    """Format active task context for the Claude prompt."""
    if not active_tasks:
        return "Active tasks: none."
    last = active_tasks[-1]
    lines = [
        f"Active tasks: {len(active_tasks)}.",
        f"Most recent goal: {last.goal}",
        f"Task pattern: {last.task_pattern.value}",
    ]
    if last.known_fields:
        lines.append(f"Already known: {last.known_fields}")
    if last.missing_fields:
        lines.append(f"Still missing: {last.missing_fields}")
    return "\n".join(lines)


def _call_claude_once(client, messages: list) -> tuple[dict, dict | None]:
    """
    Make one Claude API call and return (raw_tool_input, usage | None).

    Module-level so tests can patch it without touching the Anthropic SDK:
        monkeypatch.setattr(
            "luna.reasoning.planner._call_claude_once",
            lambda client, msgs: (raw_dict, None),
        )

    usage dict has keys "input_tokens" and "output_tokens" when available.
    Raises ValueError if Claude does not return a plan_travel_action tool call.
    """
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=settings.anthropic_max_tokens,
        system=_SYSTEM_PROMPT,
        messages=messages,
        tools=[_PLANNER_TOOL],
        tool_choice={"type": "any"},
    )
    usage: dict | None = None
    try:
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    except AttributeError:
        pass
    for block in response.content:
        if block.type == "tool_use" and block.name == "plan_travel_action":
            return block.input, usage
    raise ValueError("Claude did not return a plan_travel_action tool call")


def _run_claude(body: str, user_profile, active_tasks: list, td: dict) -> PlannerOutput:
    """
    Call Claude to produce a validated PlannerOutput.

    td is a mutable dict owned by run(). _run_claude populates it with
    retry_count, input_tokens, output_tokens, and validation_error so that
    run() retains partial trace data even if this function raises.

    Retries once with a stricter repair prompt if the first response fails
    Pydantic validation. Raises on second failure so run() can fall back.
    """
    import anthropic  # lazy — only reached when USE_CLAUDE_PLANNER=true
    from pydantic import ValidationError

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    context = _build_context(active_tasks)

    messages: list[dict] = [
        {"role": "user", "content": f"{context}\n\nUser SMS: {body}"}
    ]

    # Attempt 1 ───────────────────────────────────────────────────────────────
    first_error: str = ""
    try:
        raw, usage = _call_claude_once(client, messages)
        if usage:
            td["input_tokens"] = usage.get("input_tokens")
            td["output_tokens"] = usage.get("output_tokens")
        return PlannerOutput(**raw)
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        first_error = str(exc)[:300]
        td["validation_error"] = first_error
        td["retry_count"] = 1

    # Attempt 2 — stricter repair prompt ──────────────────────────────────────
    repair_messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"{context}\n\nUser SMS: {body}\n\n"
                "IMPORTANT: Your previous plan_travel_action call failed schema "
                f"validation. Error: {first_error}. "
                "Call plan_travel_action again. Every required field must be present "
                "and correctly typed. task_pattern must be one of the allowed enum "
                "values. known_fields must be an object. missing_fields and "
                "candidate_tools and selected_tools must be arrays of strings."
            ),
        }
    ]
    # Let any exception propagate — run() will catch and fall back.
    # td["retry_count"] is already 1 so trace data is preserved on failure.
    raw, usage = _call_claude_once(client, repair_messages)
    if usage:
        td["input_tokens"] = usage.get("input_tokens")
        td["output_tokens"] = usage.get("output_tokens")
    return PlannerOutput(**raw)


# ── Fallback planner ──────────────────────────────────────────────────────────

_WEATHER_KW = ["weather", "temperature", "forecast", "climate", "rain", "snow", "sunny"]
_FLIGHT_KW  = ["flight", "fly", "plane", "airport", "airline", "depart", "arrive"]
_HOTEL_KW   = ["hotel", "stay", "accommodation", "hostel", "airbnb", "motel", "resort", "lodge"]
_EVENTS_KW  = ["event", "concert", "show", "restaurant", "reservation", "ticket",
               "festival", "tour", "activity"]

_RE_FROM_TO = re.compile(r"\bfrom\s+([a-z ]+?)\s+to\s+([a-z ]+?)(?:\b|$)", re.IGNORECASE)
_RE_TO      = re.compile(r"\bto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)")
_RE_IN      = re.compile(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)")


def _extract_known_fields(body: str) -> dict:
    """Extract location fields from natural language using regex."""
    fields: dict = {}
    m = _RE_FROM_TO.search(body)
    if m:
        fields["origin"] = m.group(1).strip().title()
        fields["destination"] = m.group(2).strip().title()
        return fields
    m = _RE_TO.search(body)
    if m:
        fields["destination"] = m.group(1).strip()
    m = _RE_IN.search(body)
    if m:
        fields["city"] = m.group(1).strip()
    return fields


def _run_fallback(body: str) -> PlannerOutput:
    b = body.lower()
    known = _extract_known_fields(body)

    if any(kw in b for kw in _WEATHER_KW):
        missing = [f for f in ["city", "date"] if f not in known]
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.answer_with_context,
            known_fields=known,
            missing_fields=missing,
            candidate_tools=["weather_lookup"],
            selected_tools=["weather_lookup"] if "city" in known else [],
            risk_level=RiskLevel.low,
            next_action="execute_tool" if "city" in known else "ask_clarification",
            reply_draft="I can check travel weather for that. What city and date should I use?",
        )

    if any(kw in b for kw in _FLIGHT_KW):
        all_fields = ["origin", "destination", "depart_date", "return_date", "passengers"]
        missing = [f for f in all_fields if f not in known]
        can_search = "origin" in known and "destination" in known
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields=known,
            missing_fields=missing,
            candidate_tools=["flight_search"],
            selected_tools=["flight_search"] if can_search else [],
            risk_level=RiskLevel.low,
            next_action="execute_tool" if can_search else "ask_clarification",
            reply_draft="I can help compare flights. What route and dates should I search?",
        )

    if any(kw in b for kw in _HOTEL_KW):
        all_fields = ["city", "check_in", "check_out", "guests", "budget"]
        missing = [f for f in all_fields if f not in known]
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields=known,
            missing_fields=missing,
            candidate_tools=["hotel_search"],
            selected_tools=["hotel_search"] if "city" in known else [],
            risk_level=RiskLevel.low,
            next_action="execute_tool" if "city" in known else "ask_clarification",
            reply_draft="I can help compare hotels. What city, dates, and budget should I use?",
        )

    if any(kw in b for kw in _EVENTS_KW):
        all_fields = ["city", "dates", "event_type"]
        missing = [f for f in all_fields if f not in known]
        return PlannerOutput(
            goal=body,
            task_pattern=TaskPattern.search_and_compare,
            known_fields=known,
            missing_fields=missing,
            candidate_tools=["events_search"],
            selected_tools=["events_search"] if "city" in known else [],
            risk_level=RiskLevel.low,
            next_action="execute_tool" if "city" in known else "ask_clarification",
            reply_draft="I can help find travel events. Which city and dates should I check?",
        )

    return PlannerOutput(
        goal=body,
        task_pattern=TaskPattern.ask_clarification,
        known_fields={},
        missing_fields=["travel_intent"],
        candidate_tools=[],
        selected_tools=[],
        risk_level=RiskLevel.low,
        next_action="ask_clarification",
        reply_draft=(
            "I'm Luna, your SMS travel operator. "
            "Tell me what trip or destination you want help with."
        ),
    )
