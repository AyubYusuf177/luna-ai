"""
tests/test_planner_eval.py — Planner Evaluation Suite (v0.2.2).

Loads structured eval cases from tests/fixtures/planner_eval_cases.json and
validates that the planner produces correct PlannerOutput for realistic travel
requests.

Two test modes:
  1. Fallback planner  — deterministic; used for cases where keyword/regex is
                         sufficient (weather with city, flight with route, etc.)
  2. Mocked Claude     — _call_claude_once is patched to return a canned payload
                         representing expected Claude reasoning; used for messy,
                         multi-constraint cases that need frontier-model logic.

No real Anthropic API calls are made. All Claude-mode tests patch at the
_call_claude_once boundary, keeping tests deterministic and free.

_call_claude_once returns (raw_dict, usage | None). Mocks return (raw, None).
"""

import json
from pathlib import Path

import pytest

import luna.config as config_module
import luna.reasoning.planner as planner_module
from luna.agent.schemas import PlannerOutput, RiskLevel, TaskPattern
from luna.events import logger as events
from luna.memory import store as memory
from luna.reasoning.planner import run

# ── Load fixture ──────────────────────────────────────────────────────────────

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "planner_eval_cases.json"
_EVAL_CASES: list[dict] = json.loads(_FIXTURE_PATH.read_text())


# ── Helpers ───────────────────────────────────────────────────────────────────

class _FakeUser:
    user_id = "+447700000001"


def _assert_eval(result: PlannerOutput, case: dict) -> None:
    """
    Validate a PlannerOutput against an eval case using "contains" checks.
    No exact full-dict equality — eval cases specify what must be present,
    not the exhaustive ground truth.
    """
    case_id = case["id"]

    # task_pattern
    assert result.task_pattern.value == case["expected_task_pattern"], (
        f"[{case_id}] task_pattern: got {result.task_pattern.value!r}, "
        f"expected {case['expected_task_pattern']!r}"
    )

    # risk_level
    assert result.risk_level.value == case["expected_risk_level"], (
        f"[{case_id}] risk_level: got {result.risk_level.value!r}, "
        f"expected {case['expected_risk_level']!r}"
    )

    # next_action — must be one of the allowed values
    allowed_actions = case["expected_next_action_any"]
    assert result.next_action in allowed_actions, (
        f"[{case_id}] next_action: got {result.next_action!r}, "
        f"expected one of {allowed_actions}"
    )

    # known_fields — check that expected keys/values are present (subset check)
    for key, val in case["expected_known_fields_any"].items():
        assert key in result.known_fields, (
            f"[{case_id}] known_fields missing key {key!r}"
        )
        actual_val = result.known_fields[key]
        if isinstance(val, list):
            # Each expected item must appear somewhere in the actual list
            for item in val:
                assert item in actual_val, (
                    f"[{case_id}] known_fields[{key!r}]: {item!r} not in {actual_val!r}"
                )
        elif isinstance(val, str):
            # String values: check as case-insensitive substring
            assert val.lower() in str(actual_val).lower(), (
                f"[{case_id}] known_fields[{key!r}]: expected {val!r} in {actual_val!r}"
            )
        # numeric / other types: exact match
        elif val is not None:
            assert actual_val == val or str(actual_val) == str(val), (
                f"[{case_id}] known_fields[{key!r}]: got {actual_val!r}, expected {val!r}"
            )

    # missing_fields — each expected item must appear in result
    for field in case["expected_missing_fields_any"]:
        assert field in result.missing_fields, (
            f"[{case_id}] missing_fields: expected {field!r} in {result.missing_fields}"
        )

    # candidate_tools — each expected tool must appear
    for tool in case["expected_candidate_tools_any"]:
        assert tool in result.candidate_tools, (
            f"[{case_id}] candidate_tools: expected {tool!r} in {result.candidate_tools}"
        )

    # selected_tools — each expected tool must appear (empty list means none required)
    for tool in case["expected_selected_tools_any"]:
        assert tool in result.selected_tools, (
            f"[{case_id}] selected_tools: expected {tool!r} in {result.selected_tools}"
        )

    # reply_draft — must be non-empty and SMS-length
    assert result.reply_draft, f"[{case_id}] reply_draft is empty"
    assert len(result.reply_draft) <= 280, (
        f"[{case_id}] reply_draft too long: {len(result.reply_draft)} chars"
    )


def _make_claude_raw(case: dict) -> dict:
    """
    Build a canned plan_travel_action payload from an eval case.
    Returns a plain dict (not a tuple). Wrap with _mock() to use as a patch.
    """
    missing = case["expected_missing_fields_any"]
    if missing:
        reply = f"To help with that I need your {missing[0].replace('_', ' ')}."
    elif case["expected_next_action_any"][0] in ("execute_tool", "send_reply"):
        reply = "On it — searching now."
    else:
        reply = "Let me look into that for you."

    return {
        "goal": case["user_message"],
        "task_pattern": case["expected_task_pattern"],
        "known_fields": case["expected_known_fields_any"],
        "missing_fields": case["expected_missing_fields_any"],
        "candidate_tools": case["expected_candidate_tools_any"],
        "selected_tools": case["expected_selected_tools_any"],
        "risk_level": case["expected_risk_level"],
        "next_action": case["expected_next_action_any"][0],
        "reply_draft": reply,
    }


def _mock(raw: dict):
    """Wrap a raw dict into the (raw, None) tuple _call_claude_once returns."""
    return lambda client, msgs: (raw, None)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


@pytest.fixture()
def enable_claude(monkeypatch):
    monkeypatch.setattr(config_module.settings, "use_claude_planner", True)
    monkeypatch.setattr(config_module.settings, "anthropic_api_key", "test-key-xxx")


# ── Fixture integrity ─────────────────────────────────────────────────────────

def test_fixture_loads():
    assert len(_EVAL_CASES) > 0, "Eval fixture is empty"


def test_fixture_all_cases_have_required_keys():
    required = {
        "id", "category", "user_message",
        "expected_task_pattern", "expected_known_fields_any",
        "expected_missing_fields_any", "expected_candidate_tools_any",
        "expected_selected_tools_any", "expected_risk_level",
        "expected_next_action_any",
    }
    for case in _EVAL_CASES:
        missing = required - case.keys()
        assert not missing, f"Case {case.get('id', '?')} missing keys: {missing}"


def test_fixture_all_ids_unique():
    ids = [c["id"] for c in _EVAL_CASES]
    assert len(ids) == len(set(ids)), "Duplicate eval case IDs found"


def test_fixture_case_count():
    assert len(_EVAL_CASES) >= 25, f"Expected at least 25 eval cases, got {len(_EVAL_CASES)}"


def test_fixture_categories_covered():
    categories = {c["category"] for c in _EVAL_CASES}
    expected = {
        "broad_trip_planning", "flight_search", "hotel_search",
        "compound_travel_planning", "weather_lookup", "events_local_discovery",
        "monitor_alert", "transport_ride", "booking_handoff",
        "unsafe_payment_passport", "off_topic", "regression",
    }
    missing = expected - categories
    assert not missing, f"Missing eval categories: {missing}"


# ── Fallback planner evals ────────────────────────────────────────────────────
# These cases work with deterministic keyword/regex matching.

@pytest.mark.parametrize("case", [
    c for c in _EVAL_CASES if c["id"] in {
        "weather-001", "weather-002",
        "flight-001", "flight-003",
        "hotel-002",
        "events-001", "events-002",
    }
], ids=lambda c: c["id"])
def test_fallback_planner_eval(case):
    """Fallback planner produces valid output for cases with clear keywords."""
    result = run(case["user_message"], _FakeUser(), [])
    assert isinstance(result, PlannerOutput)
    # Fallback planner is allowed to differ on task_pattern for complex cases,
    # but must always return a valid PlannerOutput with non-empty reply_draft.
    assert result.reply_draft
    assert len(result.reply_draft) <= 280


# ── Mocked Claude planner evals ───────────────────────────────────────────────
# _call_claude_once returns a canned payload derived from the eval case.
# This tests the full Claude planner path (routing, validation, output) without
# any real API calls.

@pytest.mark.parametrize("case", _EVAL_CASES, ids=lambda c: c["id"])
def test_claude_planner_eval(case, enable_claude, monkeypatch):
    """Claude planner path produces PlannerOutput that satisfies eval expectations."""
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    _assert_eval(result, case)


# ── Category-level tests ──────────────────────────────────────────────────────

def _cases_by_category(cat: str) -> list[dict]:
    return [c for c in _EVAL_CASES if c["category"] == cat]


def test_all_broad_trip_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("broad_trip_planning"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_flight_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("flight_search"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_hotel_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("hotel_search"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_compound_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("compound_travel_planning"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_weather_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("weather_lookup"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_events_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("events_local_discovery"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_monitor_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("monitor_alert"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_transport_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("transport_ride"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_booking_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("booking_handoff"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_unsafe_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("unsafe_payment_passport"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


def test_all_offtopic_cases(enable_claude, monkeypatch):
    for case in _cases_by_category("off_topic"):
        raw = _make_claude_raw(case)
        monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
        result = run(case["user_message"], _FakeUser(), [])
        _assert_eval(result, case)


# ── Regression tests — manually verified with real Claude API ─────────────────

def test_regression_warm_june_asks_for_origin(enable_claude, monkeypatch):
    """Verified manually: warm/June/£500/not-Spain → planner asks for origin."""
    case = next(c for c in _EVAL_CASES if c["id"] == "regression-001")
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert result.task_pattern == TaskPattern.search_and_compare
    assert "origin" in result.missing_fields
    assert result.selected_tools == []
    assert result.next_action == "ask_clarification"


def test_regression_rome_compound_hotel_selected(enable_claude, monkeypatch):
    """Verified manually: Rome 9pm compound request → hotel_search selected, events candidate."""
    case = next(c for c in _EVAL_CASES if c["id"] == "regression-002")
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert result.task_pattern == TaskPattern.search_and_compare
    assert "hotel_search" in result.candidate_tools
    assert "events_search" in result.candidate_tools
    assert "hotel_search" in result.selected_tools


def test_regression_tokyo_monitor_pattern(enable_claude, monkeypatch):
    """Verified manually: Tokyo October monitor → monitor_and_alert, asks for origin."""
    case = next(c for c in _EVAL_CASES if c["id"] == "regression-003")
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert result.task_pattern == TaskPattern.monitor_and_alert
    assert "origin" in result.missing_fields
    assert result.selected_tools == []


# ── Structural guarantees across all cases ────────────────────────────────────

@pytest.mark.parametrize("case", _EVAL_CASES, ids=lambda c: c["id"])
def test_reply_draft_always_non_empty(case, enable_claude, monkeypatch):
    """Every eval case must produce a non-empty reply_draft."""
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert result.reply_draft


@pytest.mark.parametrize("case", _EVAL_CASES, ids=lambda c: c["id"])
def test_reply_draft_within_sms_limit(case, enable_claude, monkeypatch):
    """Every eval case reply_draft must fit within 280 characters."""
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert len(result.reply_draft) <= 280, (
        f"[{case['id']}] reply_draft too long: {len(result.reply_draft)} chars"
    )


@pytest.mark.parametrize("case", _EVAL_CASES, ids=lambda c: c["id"])
def test_result_is_planner_output_instance(case, enable_claude, monkeypatch):
    """run() must always return a PlannerOutput instance."""
    raw = _make_claude_raw(case)
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(raw))
    result = run(case["user_message"], _FakeUser(), [])
    assert isinstance(result, PlannerOutput)
