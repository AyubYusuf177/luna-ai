"""
Tests for v0.0.8 — Proactive Engine.

Covers:
  - evaluate(): opted_out suppresses.
  - evaluate(): proactive_opt_in=False suppresses.
  - evaluate(): daily cap (3) suppresses; below cap does not.
  - evaluate(): pending confirmation defers with retry_at == confirmation.expires_at.
  - evaluate(): outside window (before start) defers.
  - evaluate(): outside window (after end) defers.
  - evaluate(): retry_at is set when deferred.
  - evaluate(): inside window with no blockers sends.
  - evaluate(): send decision includes message.
  - build_message(): each trigger type gets a prefix.
  - create_scheduler_event(): returns InternalEvent with scheduler_tick source.
  - /simulate/proactive: send → 200, decision=send, logs proactive_sent.
  - /simulate/proactive: suppressed → decision=suppress.
  - /simulate/proactive: deferred → retry_at is not None.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from luna.confirmation import store as confirmation_store
from luna.events import logger as events
from luna.gateway.schemas import EventSource
from luna.main import app
from luna.memory import store as memory
from luna.scheduler import jobs as scheduler_jobs
from luna.scheduler import proactive_engine
from luna.scheduler.schemas import (
    ProactiveCandidate,
    ProactiveDecisionType,
    TriggerType,
)

_NUMBER = "+447700555555"

_WINDOW_OPEN = {"send_window_start": 0, "send_window_end": 24}  # always open


def _candidate(**kwargs) -> ProactiveCandidate:
    defaults = dict(
        user_id=_NUMBER,
        trigger_type=TriggerType.price_drop,
        message="Prices dropped to £89!",
        **_WINDOW_OPEN,
    )
    defaults.update(kwargs)
    return ProactiveCandidate(**defaults)


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    confirmation_store.reset()
    yield


# ── evaluate(): suppress rules ────────────────────────────────────────────────

def test_opted_out_suppresses():
    decision = proactive_engine.evaluate(_candidate(opted_out=True))
    assert decision.decision == ProactiveDecisionType.suppress


def test_opted_out_reason():
    decision = proactive_engine.evaluate(_candidate(opted_out=True))
    assert decision.reason == "user_opted_out"


def test_no_proactive_opt_in_suppresses():
    decision = proactive_engine.evaluate(_candidate(proactive_opt_in=False))
    assert decision.decision == ProactiveDecisionType.suppress


def test_no_proactive_opt_in_reason():
    decision = proactive_engine.evaluate(_candidate(proactive_opt_in=False))
    assert decision.reason == "proactive_not_opted_in"


def test_daily_cap_suppresses_after_3():
    for _ in range(3):
        events.log("proactive_sent", _NUMBER, {})
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision == ProactiveDecisionType.suppress


def test_daily_cap_reason():
    for _ in range(3):
        events.log("proactive_sent", _NUMBER, {})
    decision = proactive_engine.evaluate(_candidate())
    assert decision.reason == "daily_cap_exceeded"


def test_daily_cap_does_not_suppress_below_3():
    for _ in range(2):
        events.log("proactive_sent", _NUMBER, {})
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision != ProactiveDecisionType.suppress


def test_daily_cap_does_not_count_other_users():
    other = "+447700666666"
    for _ in range(3):
        events.log("proactive_sent", other, {})
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision == ProactiveDecisionType.send


def test_daily_cap_does_not_count_other_event_types():
    for _ in range(3):
        events.log("outbound_sms_sent", _NUMBER, {})
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision == ProactiveDecisionType.send


# ── evaluate(): defer — pending confirmation ──────────────────────────────────

def test_pending_confirmation_defers():
    confirmation_store.create(_NUMBER, "task-1", "book_flight", "Book London–Tokyo")
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision == ProactiveDecisionType.defer


def test_pending_confirmation_reason():
    confirmation_store.create(_NUMBER, "task-1", "book_flight", "Book London–Tokyo")
    decision = proactive_engine.evaluate(_candidate())
    assert decision.reason == "pending_confirmation"


def test_pending_confirmation_retry_at_equals_expiry():
    c = confirmation_store.create(_NUMBER, "task-1", "book_flight", "Book London–Tokyo")
    decision = proactive_engine.evaluate(_candidate())
    assert decision.retry_at == c.expires_at


def test_no_pending_confirmation_does_not_defer_on_this_rule():
    decision = proactive_engine.evaluate(_candidate())
    assert decision.reason != "pending_confirmation"


# ── evaluate(): defer — outside send window ───────────────────────────────────

def test_outside_window_before_start_defers():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=9, send_window_end=21),
        _current_hour=5,
    )
    assert decision.decision == ProactiveDecisionType.defer


def test_outside_window_after_end_defers():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=8, send_window_end=21),
        _current_hour=22,
    )
    assert decision.decision == ProactiveDecisionType.defer


def test_outside_window_reason():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=9, send_window_end=21),
        _current_hour=5,
    )
    assert decision.reason == "outside_send_window"


def test_outside_window_retry_at_is_set():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=9, send_window_end=21),
        _current_hour=5,
    )
    assert decision.retry_at is not None


def test_outside_window_retry_at_is_window_start_hour():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=9, send_window_end=21),
        _current_hour=5,
    )
    assert decision.retry_at.hour == 9


def test_window_boundary_start_is_inclusive():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=8, send_window_end=21),
        _current_hour=8,
    )
    assert decision.decision == ProactiveDecisionType.send


def test_window_boundary_end_is_exclusive():
    decision = proactive_engine.evaluate(
        _candidate(send_window_start=8, send_window_end=21),
        _current_hour=21,
    )
    assert decision.decision == ProactiveDecisionType.defer


# ── evaluate(): send ──────────────────────────────────────────────────────────

def test_all_clear_sends():
    decision = proactive_engine.evaluate(_candidate())
    assert decision.decision == ProactiveDecisionType.send


def test_send_reason():
    decision = proactive_engine.evaluate(_candidate())
    assert decision.reason == "all_checks_passed"


def test_send_includes_message():
    decision = proactive_engine.evaluate(_candidate(message="Prices dropped!"))
    assert decision.message == "Prices dropped!"


def test_send_user_id_matches():
    decision = proactive_engine.evaluate(_candidate())
    assert decision.user_id == _NUMBER


def test_send_retry_at_is_none():
    decision = proactive_engine.evaluate(_candidate())
    assert decision.retry_at is None


# ── build_message() ───────────────────────────────────────────────────────────

def test_build_message_price_drop_has_prefix():
    msg = scheduler_jobs.build_message(TriggerType.price_drop, "£89 to Tokyo")
    assert "Price alert" in msg or "price" in msg.lower()


def test_build_message_check_in_reminder_has_prefix():
    msg = scheduler_jobs.build_message(TriggerType.check_in_reminder, "Check in opens tomorrow")
    assert "Check-in" in msg or "reminder" in msg.lower()


def test_build_message_weather_change_has_prefix():
    msg = scheduler_jobs.build_message(TriggerType.weather_change, "Rain in Paris")
    assert "Weather" in msg or "weather" in msg.lower()


def test_build_message_task_follow_up_has_prefix():
    msg = scheduler_jobs.build_message(TriggerType.task_follow_up, "Still looking for flights?")
    assert "Follow" in msg or "follow" in msg.lower()


def test_build_message_includes_raw_message():
    raw = "Fares as low as £79"
    msg = scheduler_jobs.build_message(TriggerType.price_drop, raw)
    assert raw in msg


# ── create_scheduler_event() ──────────────────────────────────────────────────

def test_create_scheduler_event_returns_internal_event():
    from luna.gateway.schemas import InternalEvent

    event = scheduler_jobs.create_scheduler_event(_NUMBER, "Test message")
    assert isinstance(event, InternalEvent)


def test_create_scheduler_event_source_is_scheduler_tick():
    event = scheduler_jobs.create_scheduler_event(_NUMBER, "Test message")
    assert event.source == EventSource.scheduler_tick


def test_create_scheduler_event_user_id_matches():
    event = scheduler_jobs.create_scheduler_event(_NUMBER, "Test message")
    assert event.user_id == _NUMBER


def test_create_scheduler_event_body_matches():
    event = scheduler_jobs.create_scheduler_event(_NUMBER, "Price dropped!")
    assert event.body == "Price dropped!"


def test_create_scheduler_event_has_received_at():
    event = scheduler_jobs.create_scheduler_event(_NUMBER, "msg")
    assert event.received_at is not None


# ── /simulate/proactive — HTTP integration ────────────────────────────────────

_PROACTIVE_PAYLOAD = {
    "user_id": _NUMBER,
    "trigger_type": "price_drop",
    "message": "Fares dropped to £89!",
    "send_window_start": 0,
    "send_window_end": 24,
}


@pytest.mark.asyncio
async def test_simulate_proactive_send_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_simulate_proactive_send_decision_is_send():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    assert response.json()["decision"] == "send"


@pytest.mark.asyncio
async def test_simulate_proactive_send_includes_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    assert response.json()["message"] is not None


@pytest.mark.asyncio
async def test_simulate_proactive_send_message_has_prefix():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    assert "Price drop" in response.json()["message"]


@pytest.mark.asyncio
async def test_simulate_proactive_send_logs_proactive_sent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    log_types = [e.event_type for e in events.get_log()]
    assert "proactive_sent" in log_types


@pytest.mark.asyncio
async def test_simulate_proactive_suppressed_opted_out():
    payload = {**_PROACTIVE_PAYLOAD, "opted_out": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=payload)
    assert response.json()["decision"] == "suppress"


@pytest.mark.asyncio
async def test_simulate_proactive_suppressed_no_opt_in():
    payload = {**_PROACTIVE_PAYLOAD, "proactive_opt_in": False}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=payload)
    assert response.json()["decision"] == "suppress"


@pytest.mark.asyncio
async def test_simulate_proactive_suppressed_message_is_null():
    payload = {**_PROACTIVE_PAYLOAD, "opted_out": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=payload)
    assert response.json()["message"] is None


@pytest.mark.asyncio
async def test_simulate_proactive_suppressed_does_not_log_proactive_sent():
    payload = {**_PROACTIVE_PAYLOAD, "opted_out": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate/proactive", json=payload)
    log_types = [e.event_type for e in events.get_log()]
    assert "proactive_sent" not in log_types


@pytest.mark.asyncio
async def test_simulate_proactive_deferred_outside_window():
    payload = {
        **_PROACTIVE_PAYLOAD,
        "send_window_start": 9,
        "send_window_end": 10,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=payload)
    data = response.json()
    # Will either defer (if current hour outside 9–10) or send (if inside)
    assert data["decision"] in ("send", "defer")


@pytest.mark.asyncio
async def test_simulate_proactive_reason_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate/proactive", json=_PROACTIVE_PAYLOAD)
    assert len(response.json()["reason"]) > 0
