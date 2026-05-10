"""
Tests for the Claude-powered planner path in luna/reasoning/planner.py — v0.2.0.

Real Anthropic API calls never happen in these tests because:
  - All tests either leave USE_CLAUDE_PLANNER=false (default), or
  - Patch luna.reasoning.planner._call_claude_once to return a canned dict.

The _call_claude_once function is module-level specifically to enable this
clean monkeypatching pattern without mocking the Anthropic SDK constructor.
"""

import pytest

import luna.config as config_module
from luna.agent.schemas import PlannerOutput, RiskLevel, TaskPattern
from luna.events import logger as events
from luna.memory import store as memory
import luna.reasoning.planner as planner_module
from luna.reasoning.planner import run


# ── Fixtures ──────────────────────────────────────────────────────────────────

class _FakeUser:
    user_id = "+447700000000"


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


@pytest.fixture()
def enable_claude(monkeypatch):
    """Enable the Claude planner path without a real API key."""
    monkeypatch.setattr(config_module.settings, "use_claude_planner", True)
    monkeypatch.setattr(config_module.settings, "anthropic_api_key", "test-key-xxx")


def _valid_raw(**overrides) -> dict:
    """Return a minimal valid plan_travel_action payload."""
    base = {
        "goal": "Find flights from London to Rome",
        "task_pattern": "search_and_compare",
        "known_fields": {"origin": "London", "destination": "Rome"},
        "missing_fields": ["depart_date", "return_date", "passengers"],
        "candidate_tools": ["flight_search"],
        "selected_tools": ["flight_search"],
        "risk_level": "low",
        "next_action": "execute_tool",
        "reply_draft": "Searching flights from London to Rome. What dates and how many passengers?",
    }
    base.update(overrides)
    return base


# ── Fallback when Claude is disabled ─────────────────────────────────────────

def test_fallback_used_when_claude_disabled():
    """Claude path is skipped when use_claude_planner=False (default)."""
    result = run("flights to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)
    assert result.task_pattern == TaskPattern.search_and_compare


def test_fallback_used_when_no_api_key(monkeypatch):
    """Claude path is skipped when API key is absent even if flag is True."""
    monkeypatch.setattr(config_module.settings, "use_claude_planner", True)
    monkeypatch.setattr(config_module.settings, "anthropic_api_key", "")
    result = run("flights to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)


# ── Claude path: happy path ───────────────────────────────────────────────────

def test_claude_path_returns_planner_output(enable_claude, monkeypatch):
    """A valid mock response produces a PlannerOutput."""
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: _valid_raw())
    result = run("flights from London to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)
    assert result.task_pattern == TaskPattern.search_and_compare
    assert result.known_fields == {"origin": "London", "destination": "Rome"}
    assert result.selected_tools == ["flight_search"]
    assert result.risk_level == RiskLevel.low


def test_claude_path_reply_draft_preserved(enable_claude, monkeypatch):
    """reply_draft from Claude is returned as-is."""
    raw = _valid_raw(reply_draft="Searching flights now.")
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run("flights from London to Rome", _FakeUser(), [])
    assert result.reply_draft == "Searching flights now."


def test_claude_path_no_real_api_call(enable_claude, monkeypatch):
    """Patching _call_claude_once prevents any real network call."""
    called = []

    def mock_claude(client, msgs):
        called.append(msgs)
        return _valid_raw()

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    run("flights from London to Rome", _FakeUser(), [])
    assert len(called) == 1


# ── Claude path: retry logic ──────────────────────────────────────────────────

def test_retry_on_malformed_first_response(enable_claude, monkeypatch):
    """Bad first response → retry → valid second response → success."""
    call_count = []

    def mock_claude(client, msgs):
        call_count.append(1)
        if len(call_count) == 1:
            return {"goal": "incomplete"}  # missing required fields → ValidationError
        return _valid_raw()

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    result = run("flights from London to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)
    assert len(call_count) == 2


def test_repair_prompt_contains_error_detail(enable_claude, monkeypatch):
    """Second call receives a repair prompt mentioning the validation error."""
    messages_seen = []

    def mock_claude(client, msgs):
        messages_seen.append(msgs[0]["content"])
        if len(messages_seen) == 1:
            return {"goal": "bad"}
        return _valid_raw()

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    run("flights from London to Rome", _FakeUser(), [])
    assert len(messages_seen) == 2
    assert "IMPORTANT" in messages_seen[1]
    assert "validation" in messages_seen[1].lower()


def test_fallback_after_two_bad_responses(enable_claude, monkeypatch):
    """Both attempts return malformed data → fallback planner used."""
    monkeypatch.setattr(
        planner_module,
        "_call_claude_once",
        lambda client, msgs: {"goal": "bad"},  # always malformed
    )
    result = run("flights from London to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)  # fallback still returns valid output


def test_planner_fallback_event_logged(enable_claude, monkeypatch):
    """planner_fallback_used event is logged when Claude path fails."""
    monkeypatch.setattr(
        planner_module,
        "_call_claude_once",
        lambda client, msgs: {"goal": "bad"},
    )
    run("flights from London to Rome", _FakeUser(), [])
    fallback_events = [
        e for e in events.get_log() if e.event_type == "planner_fallback_used"
    ]
    assert len(fallback_events) == 1
    assert fallback_events[0].metadata["reason"] == "claude_planner_failed"


def test_planner_fallback_event_has_correct_uid(enable_claude, monkeypatch):
    """planner_fallback_used event carries the user's uid."""
    monkeypatch.setattr(
        planner_module,
        "_call_claude_once",
        lambda client, msgs: {"goal": "bad"},
    )
    user = _FakeUser()
    run("flights from London to Rome", user, [])
    fallback_events = [
        e for e in events.get_log() if e.event_type == "planner_fallback_used"
    ]
    assert fallback_events[0].user_id == user.user_id


# ── Schema validation ─────────────────────────────────────────────────────────

def test_all_task_patterns_accepted(enable_claude, monkeypatch):
    """Claude may return any TaskPattern value without raising."""
    for pattern in TaskPattern:
        raw = _valid_raw(
            task_pattern=pattern.value,
            selected_tools=[],
            next_action="ask_clarification",
        )
        monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs, r=raw: r)
        result = run("some travel request", _FakeUser(), [])
        assert result.task_pattern == pattern


def test_risk_levels_accepted(enable_claude, monkeypatch):
    """All three risk levels are accepted by PlannerOutput."""
    for level in ("low", "medium", "high"):
        raw = _valid_raw(risk_level=level)
        monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs, r=raw: r)
        result = run("book a flight", _FakeUser(), [])
        assert result.risk_level.value == level


def test_empty_selected_tools_valid(enable_claude, monkeypatch):
    """selected_tools may be empty when required args are missing."""
    raw = _valid_raw(
        selected_tools=[],
        next_action="ask_clarification",
        reply_draft="Where are you flying from?",
    )
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run("I want to fly somewhere", _FakeUser(), [])
    assert result.selected_tools == []
    assert result.next_action == "ask_clarification"


# ── Messy real-world request examples ────────────────────────────────────────

def test_warm_june_budget_request(enable_claude, monkeypatch):
    """'somewhere warm in June under £500 not Spain' — constraint extraction."""
    raw = _valid_raw(
        goal="Find a warm destination in June under £500 excluding Spain",
        task_pattern="search_and_compare",
        known_fields={
            "month": "June",
            "budget_max": 500,
            "climate": "warm",
            "excluded_destinations": ["Spain"],
        },
        missing_fields=["origin", "destination"],
        candidate_tools=["flight_search"],
        selected_tools=[],
        next_action="ask_clarification",
        reply_draft="Where would you be flying from?",
    )
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run("somewhere warm in June under £500 not Spain", _FakeUser(), [])
    assert result.known_fields["climate"] == "warm"
    assert "Spain" in result.known_fields["excluded_destinations"]
    assert result.selected_tools == []


def test_rome_arrival_multi_tool(enable_claude, monkeypatch):
    """'I land in Rome at 9pm' — hotel + events candidate with hotel selected."""
    raw = _valid_raw(
        goal="Find a hotel near Rome station and a relaxed morning activity",
        task_pattern="search_and_compare",
        known_fields={
            "destination": "Rome",
            "arrival_time": "21:00",
            "hotel_preference": "near station",
            "activity_preference": "relaxed morning activity",
        },
        missing_fields=[],
        candidate_tools=["hotel_search", "events_search"],
        selected_tools=["hotel_search"],
        next_action="execute_tool",
        reply_draft="Finding hotels near Rome station and morning activities.",
    )
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run(
        "I land in Rome at 9pm, need a hotel near the station and something relaxed in the morning",
        _FakeUser(),
        [],
    )
    assert "hotel_search" in result.candidate_tools
    assert "events_search" in result.candidate_tools
    assert result.selected_tools == ["hotel_search"]


def test_tokyo_monitor_pattern(enable_claude, monkeypatch):
    """'Keep an eye on Tokyo for October' → monitor_and_alert pattern."""
    raw = _valid_raw(
        goal="Monitor Tokyo flights for October and alert if meaningfully cheaper",
        task_pattern="monitor_and_alert",
        known_fields={
            "destination": "Tokyo",
            "date_window": "October",
            "alert_condition": "meaningfully cheaper than usual",
        },
        missing_fields=["origin"],
        candidate_tools=["flight_search"],
        selected_tools=[],
        next_action="ask_clarification",
        reply_draft="I'll watch Tokyo for October. Where would you be flying from?",
    )
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run(
        "Keep an eye on Tokyo for October, only tell me if meaningfully cheaper",
        _FakeUser(),
        [],
    )
    assert result.task_pattern == TaskPattern.monitor_and_alert
    assert result.known_fields["destination"] == "Tokyo"
    assert "origin" in result.missing_fields


def test_uber_booking_confirmation_required(enable_claude, monkeypatch):
    """'Book me an Uber' → confirmation_required_action, medium risk, no claim of booking."""
    raw = _valid_raw(
        goal="Book an Uber from hotel to airport at 6am tomorrow",
        task_pattern="confirmation_required_action",
        known_fields={
            "pickup": "hotel",
            "destination": "airport",
            "time": "06:00",
            "date": "tomorrow",
        },
        missing_fields=[],
        candidate_tools=[],
        selected_tools=[],
        risk_level="medium",
        next_action="create_confirmation",
        reply_draft="Uber from hotel to airport at 6am tomorrow — confirm? Reply YES or NO.",
    )
    monkeypatch.setattr(planner_module, "_call_claude_once", lambda client, msgs: raw)
    result = run(
        "Book me an Uber from my hotel to the airport at 6am tomorrow",
        _FakeUser(),
        [],
    )
    assert result.task_pattern == TaskPattern.confirmation_required_action
    assert result.risk_level == RiskLevel.medium
    assert "booked" not in result.reply_draft.lower()


# ── Active task context ───────────────────────────────────────────────────────

def test_active_task_context_included_in_prompt(enable_claude, monkeypatch):
    """Active tasks are serialised into the Claude prompt."""
    messages_seen = []

    def mock_claude(client, msgs):
        messages_seen.append(msgs[0]["content"])
        return _valid_raw()

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)

    class _FakeTask:
        goal = "Find flights to Tokyo"
        task_pattern = TaskPattern.search_and_compare
        known_fields = {"destination": "Tokyo"}
        missing_fields = ["origin"]

    run("what about dates", _FakeUser(), [_FakeTask()])
    assert "Tokyo" in messages_seen[0]
    assert "Active tasks: 1" in messages_seen[0]


def test_no_active_tasks_produces_clean_context(enable_claude, monkeypatch):
    """Empty active_tasks list results in 'Active tasks: none.' in prompt."""
    messages_seen = []

    def mock_claude(client, msgs):
        messages_seen.append(msgs[0]["content"])
        return _valid_raw()

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    run("flights to Rome", _FakeUser(), [])
    assert "Active tasks: none." in messages_seen[0]
