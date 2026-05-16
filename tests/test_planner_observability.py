"""
tests/test_planner_observability.py — Planner observability + cost controls (v0.2.2).

Tests for:
  - planner_run event emitted on every run (fallback and Claude paths)
  - Correct trace fields: planner_mode, fallback_used, retry_count, latency_ms, etc.
  - retry_count incremented when first Claude response fails validation
  - fallback_used + fallback_reason set when both Claude attempts fail
  - Cost estimator: known model + tokens → expected USD
  - Cost estimator: None for missing tokens or unknown model
  - Event metadata contains no API key, no prompt text, no PII
  - No real Anthropic API calls
"""

import pytest

import luna.config as config_module
from luna.agent.schemas import PlannerOutput, TaskPattern
from luna.events import logger as events
from luna.memory import store as memory
import luna.reasoning.planner as planner_module
from luna.reasoning.planner import PlannerTrace, _estimate_cost, run


# ── Fixtures ──────────────────────────────────────────────────────────────────

class _FakeUser:
    user_id = "+447700000099"


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


@pytest.fixture()
def enable_claude(monkeypatch):
    monkeypatch.setattr(config_module.settings, "use_claude_planner", True)
    monkeypatch.setattr(config_module.settings, "anthropic_api_key", "test-key-xxx")
    monkeypatch.setattr(config_module.settings, "anthropic_model", "claude-sonnet-4-6")


def _valid_raw(**overrides) -> dict:
    base = {
        "goal": "Find flights from London to Rome",
        "task_pattern": "search_and_compare",
        "known_fields": {"origin": "London", "destination": "Rome"},
        "missing_fields": [],
        "candidate_tools": ["flight_search"],
        "selected_tools": ["flight_search"],
        "risk_level": "low",
        "next_action": "execute_tool",
        "reply_draft": "Searching flights from London to Rome.",
    }
    base.update(overrides)
    return base


def _mock(raw: dict, usage: dict | None = None):
    return lambda client, msgs: (raw, usage)


def _get_planner_event():
    return next(
        (e for e in events.get_log() if e.event_type == "planner_run"),
        None,
    )


# ── PlannerTrace dataclass ────────────────────────────────────────────────────

def test_planner_trace_is_importable():
    assert PlannerTrace is not None


def test_planner_trace_has_expected_fields():
    t = PlannerTrace(
        planner_mode="fallback",
        used_claude=False,
        fallback_used=False,
        retry_count=0,
        latency_ms=12.5,
    )
    assert t.planner_mode == "fallback"
    assert t.model is None
    assert t.input_tokens is None
    assert t.estimated_cost_usd is None


# ── Cost estimator ────────────────────────────────────────────────────────────

def test_cost_estimator_known_model_and_tokens():
    """claude-sonnet-4-6: $3/MTok input + $15/MTok output."""
    cost = _estimate_cost("claude-sonnet-4-6", 1000, 500)
    # 1000 * 3.0 / 1_000_000 + 500 * 15.0 / 1_000_000 = 0.003 + 0.0075 = 0.0105
    assert cost == pytest.approx(0.0105, rel=1e-6)


def test_cost_estimator_zero_tokens():
    cost = _estimate_cost("claude-sonnet-4-6", 0, 0)
    assert cost == pytest.approx(0.0)


def test_cost_estimator_none_when_model_unknown():
    assert _estimate_cost("claude-unknown-99", 1000, 500) is None


def test_cost_estimator_none_when_model_is_none():
    assert _estimate_cost(None, 1000, 500) is None


def test_cost_estimator_none_when_tokens_missing():
    assert _estimate_cost("claude-sonnet-4-6", None, None) is None


def test_cost_estimator_none_when_only_input_missing():
    assert _estimate_cost("claude-sonnet-4-6", None, 500) is None


def test_cost_estimator_none_when_only_output_missing():
    assert _estimate_cost("claude-sonnet-4-6", 1000, None) is None


def test_cost_estimator_haiku_pricing():
    """claude-haiku-4-5-20251001: $0.80/MTok input + $4.00/MTok output."""
    cost = _estimate_cost("claude-haiku-4-5-20251001", 2000, 1000)
    # 2000 * 0.80 / 1_000_000 + 1000 * 4.00 / 1_000_000 = 0.0016 + 0.004 = 0.0056
    assert cost == pytest.approx(0.0056, rel=1e-6)


def test_cost_estimator_opus_pricing():
    """claude-opus-4-7: $15/MTok input + $75/MTok output."""
    cost = _estimate_cost("claude-opus-4-7", 500, 200)
    # 500 * 15.0 / 1_000_000 + 200 * 75.0 / 1_000_000 = 0.0075 + 0.015 = 0.0225
    assert cost == pytest.approx(0.0225, rel=1e-6)


# ── planner_run event — fallback path ─────────────────────────────────────────

def test_fallback_emits_planner_run_event():
    """Every run() call emits a planner_run event."""
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event() is not None


def test_fallback_event_planner_mode():
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["planner_mode"] == "fallback"


def test_fallback_event_used_claude_false():
    run("flights to Rome", _FakeUser(), [])
    # 'model' should be None in fallback mode
    assert _get_planner_event().metadata["model"] is None


def test_fallback_event_fallback_used_false():
    """fallback_used=False means we chose fallback by config, not by Claude failure."""
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["fallback_used"] is False


def test_fallback_event_retry_count_zero():
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["retry_count"] == 0


def test_fallback_event_latency_is_numeric():
    run("flights to Rome", _FakeUser(), [])
    latency = _get_planner_event().metadata["latency_ms"]
    assert isinstance(latency, (int, float))
    assert latency >= 0


def test_fallback_event_task_pattern_set():
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["task_pattern"] == "search_and_compare"


def test_fallback_event_selected_tools_list():
    run("weather in Paris", _FakeUser(), [])
    tools = _get_planner_event().metadata["selected_tools"]
    assert isinstance(tools, list)


def test_fallback_event_tokens_none():
    run("flights to Rome", _FakeUser(), [])
    meta = _get_planner_event().metadata
    assert meta["input_tokens"] is None
    assert meta["output_tokens"] is None


def test_fallback_event_cost_none():
    run("flights to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["estimated_cost_usd"] is None


def test_fallback_event_user_id_correct():
    user = _FakeUser()
    run("flights to Rome", user, [])
    assert _get_planner_event().user_id == user.user_id


# ── planner_run event — Claude success path ───────────────────────────────────

def test_claude_success_emits_planner_run_event(enable_claude, monkeypatch):
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event() is not None


def test_claude_success_event_planner_mode(enable_claude, monkeypatch):
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["planner_mode"] == "claude"


def test_claude_success_event_model_set(enable_claude, monkeypatch):
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["model"] == "claude-sonnet-4-6"


def test_claude_success_event_fallback_used_false(enable_claude, monkeypatch):
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["fallback_used"] is False


def test_claude_success_event_retry_count_zero(enable_claude, monkeypatch):
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["retry_count"] == 0


def test_claude_success_event_with_usage(enable_claude, monkeypatch):
    """When mock provides usage, tokens and cost appear in event."""
    usage = {"input_tokens": 800, "output_tokens": 300}
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw(), usage))
    run("flights from London to Rome", _FakeUser(), [])
    meta = _get_planner_event().metadata
    assert meta["input_tokens"] == 800
    assert meta["output_tokens"] == 300
    # 800 * 3.0 / 1M + 300 * 15.0 / 1M = 0.0024 + 0.0045 = 0.0069
    assert meta["estimated_cost_usd"] == pytest.approx(0.0069, rel=1e-6)


def test_claude_success_event_no_usage_tokens_none(enable_claude, monkeypatch):
    """When mock returns no usage (None), tokens remain None."""
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw(), None))
    run("flights from London to Rome", _FakeUser(), [])
    meta = _get_planner_event().metadata
    assert meta["input_tokens"] is None
    assert meta["output_tokens"] is None
    assert meta["estimated_cost_usd"] is None


# ── planner_run event — retry path ────────────────────────────────────────────

def test_retry_increments_retry_count(enable_claude, monkeypatch):
    """When the first attempt fails validation, retry_count=1 in event."""
    call_count = []

    def mock_claude(client, msgs):
        call_count.append(1)
        if len(call_count) == 1:
            return ({"goal": "bad"}, None)
        return (_valid_raw(), None)

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["retry_count"] == 1


def test_retry_planner_mode_still_claude(enable_claude, monkeypatch):
    """Even with a retry, the planner_mode is 'claude' (not fallback)."""
    call_count = []

    def mock_claude(client, msgs):
        call_count.append(1)
        if len(call_count) == 1:
            return ({"goal": "bad"}, None)
        return (_valid_raw(), None)

    monkeypatch.setattr(planner_module, "_call_claude_once", mock_claude)
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["planner_mode"] == "claude"


# ── planner_run event — double failure / fallback path ───────────────────────

def test_double_failure_fallback_used_true(enable_claude, monkeypatch):
    """Both Claude attempts fail → fallback_used=True in event."""
    monkeypatch.setattr(
        planner_module, "_call_claude_once", lambda client, msgs: ({"goal": "bad"}, None)
    )
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["fallback_used"] is True


def test_double_failure_fallback_reason_set(enable_claude, monkeypatch):
    monkeypatch.setattr(
        planner_module, "_call_claude_once", lambda client, msgs: ({"goal": "bad"}, None)
    )
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["fallback_reason"] == "claude_planner_failed"


def test_double_failure_retry_count_is_1(enable_claude, monkeypatch):
    """Two failures: retry_count captures that a retry occurred."""
    monkeypatch.setattr(
        planner_module, "_call_claude_once", lambda client, msgs: ({"goal": "bad"}, None)
    )
    run("flights from London to Rome", _FakeUser(), [])
    assert _get_planner_event().metadata["retry_count"] == 1


def test_double_failure_result_is_planner_output(enable_claude, monkeypatch):
    """Fallback after double failure still returns a valid PlannerOutput."""
    monkeypatch.setattr(
        planner_module, "_call_claude_once", lambda client, msgs: ({"goal": "bad"}, None)
    )
    result = run("flights from London to Rome", _FakeUser(), [])
    assert isinstance(result, PlannerOutput)


# ── Safety: no secrets in event metadata ─────────────────────────────────────

def test_api_key_not_in_event_metadata(enable_claude, monkeypatch):
    """The Anthropic API key must never appear in logged event metadata."""
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    meta_str = str(_get_planner_event().metadata)
    assert "test-key-xxx" not in meta_str


def test_prompt_text_not_in_event_metadata(enable_claude, monkeypatch):
    """Full prompt content must not be logged in event metadata."""
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    meta_str = str(_get_planner_event().metadata)
    # System prompt marker should not appear in event metadata
    assert "travel planning engine" not in meta_str


def test_event_metadata_safe_keys_only(enable_claude, monkeypatch):
    """Event metadata contains only the expected observability keys."""
    monkeypatch.setattr(planner_module, "_call_claude_once", _mock(_valid_raw()))
    run("flights from London to Rome", _FakeUser(), [])
    meta = _get_planner_event().metadata
    allowed_keys = {
        "planner_mode", "model", "fallback_used", "fallback_reason",
        "retry_count", "latency_ms", "input_tokens", "output_tokens",
        "estimated_cost_usd", "task_pattern", "selected_tools",
    }
    unexpected = set(meta.keys()) - allowed_keys
    assert not unexpected, f"Unexpected keys in planner_run metadata: {unexpected}"


# ── One planner_run event per run() call ──────────────────────────────────────

def test_exactly_one_planner_run_event_per_call():
    """run() emits exactly one planner_run event per invocation."""
    run("weather in Tokyo", _FakeUser(), [])
    run("hotels in Berlin", _FakeUser(), [])
    planner_events = [e for e in events.get_log() if e.event_type == "planner_run"]
    assert len(planner_events) == 2


def test_planner_run_event_before_fallback_used_event(enable_claude, monkeypatch):
    """Both planner_run and planner_fallback_used events are emitted on failure."""
    monkeypatch.setattr(
        planner_module, "_call_claude_once", lambda client, msgs: ({"goal": "bad"}, None)
    )
    run("flights from London to Rome", _FakeUser(), [])
    log_types = {e.event_type for e in events.get_log()}
    assert "planner_run" in log_types
    assert "planner_fallback_used" in log_types
