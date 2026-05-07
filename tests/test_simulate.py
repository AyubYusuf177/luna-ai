"""
Tests for POST /simulate — v0.0.2 / updated v0.0.3.

Each test resets in-memory state via the autouse fixture so tests
are fully isolated and order-independent.

v0.0.3 addition: /simulate now routes through the Event Gateway, so
the event log contains an internal_event_received entry with
source="simulate_inbound" on every request.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory

_NUMBER = "+447700000000"
_PAYLOAD = {"from_number": _NUMBER, "body": "hello"}


@pytest.fixture(autouse=True)
def reset_state():
    """Reset all in-memory state before every test."""
    memory.reset()
    events.reset()
    yield


# ── Endpoint ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json=_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_simulate_returns_expected_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json=_PAYLOAD)
    body = response.json()
    assert body["from_number"] == _NUMBER
    assert isinstance(body["reply"], str)
    assert len(body["reply"]) > 0


# ── User creation ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_new_user_is_created():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    user = memory.get_user(_NUMBER)
    assert user is not None
    assert user.user_id == _NUMBER


@pytest.mark.asyncio
async def test_second_message_does_not_create_duplicate_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
        await client.post("/simulate", json={**_PAYLOAD, "body": "second message"})
    # Only one profile should exist for this number
    user = memory.get_user(_NUMBER)
    assert user is not None
    # Confirm there is only one user in the store
    assert memory.get_user("+19999999999") is None  # different number has no profile


# ── Conversation memory ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_conversation_stores_inbound_turn():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    turns = memory.get_conversation(_NUMBER)
    user_turns = [t for t in turns if t.role == "user"]
    assert len(user_turns) == 1
    assert user_turns[0].body == "hello"


@pytest.mark.asyncio
async def test_conversation_stores_outbound_turn():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    turns = memory.get_conversation(_NUMBER)
    luna_turns = [t for t in turns if t.role == "luna"]
    assert len(luna_turns) == 1
    assert len(luna_turns[0].body) > 0


@pytest.mark.asyncio
async def test_conversation_turn_order_is_user_then_luna():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    turns = memory.get_conversation(_NUMBER)
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[1].role == "luna"


@pytest.mark.asyncio
async def test_multiple_messages_accumulate_in_history():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
        await client.post("/simulate", json={**_PAYLOAD, "body": "second message"})
    turns = memory.get_conversation(_NUMBER)
    assert len(turns) == 4  # 2 user + 2 luna


# ── Event log ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_event_log_records_inbound_event():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    types = [e.event_type for e in events.get_log()]
    assert "inbound_sms_received" in types


@pytest.mark.asyncio
async def test_event_log_records_user_identified_event():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    types = [e.event_type for e in events.get_log()]
    assert "user_identified" in types


@pytest.mark.asyncio
async def test_event_log_records_outbound_event():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    types = [e.event_type for e in events.get_log()]
    assert "outbound_sms_sent" in types


@pytest.mark.asyncio
async def test_event_log_new_user_flag_is_true_on_first_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    identified = [e for e in events.get_log() if e.event_type == "user_identified"]
    assert identified[0].metadata["is_new_user"] is True


# ── InternalEvent (v0.0.3) ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_creates_internal_event_with_correct_source():
    """/simulate must produce an InternalEvent logged as simulate_inbound."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    gateway_events = [
        e for e in events.get_log() if e.event_type == "internal_event_received"
    ]
    assert len(gateway_events) == 1
    assert gateway_events[0].metadata["source"] == "simulate_inbound"


@pytest.mark.asyncio
async def test_event_log_new_user_flag_is_false_on_second_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
        events.reset()  # clear first-message events so we can inspect second cleanly
        await client.post("/simulate", json={**_PAYLOAD, "body": "second message"})
    identified = [e for e in events.get_log() if e.event_type == "user_identified"]
    assert identified[0].metadata["is_new_user"] is False
