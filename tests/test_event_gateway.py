"""
Tests for the Event Gateway and channel adapters — v0.0.3.

Tests are split by concern:
  - Simulator channel: normalize() produces a valid InternalEvent.
  - Twilio channel: normalize() extracts From/Body correctly.
  - Event Gateway: handle() routes an InternalEvent to the runtime stub.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from luna.channels import simulator as simulator_channel
from luna.channels import twilio as twilio_channel
from luna.events import logger as events
from luna.gateway import event_gateway
from luna.gateway.schemas import EventSource, InternalEvent
from luna.main import app
from luna.memory import store as memory

_NUMBER = "+447700000000"


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


# ── Simulator channel — unit tests ────────────────────────────────────────────

def test_simulator_normalize_produces_internal_event():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert isinstance(event, InternalEvent)


def test_simulator_normalize_sets_correct_source():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert event.source == EventSource.simulate_inbound


def test_simulator_normalize_sets_user_id():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert event.user_id == _NUMBER


def test_simulator_normalize_sets_body():
    event = simulator_channel.normalize(from_number=_NUMBER, body="find flights to Tokyo")
    assert event.body == "find flights to Tokyo"


def test_simulator_normalize_sets_raw_payload():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert event.raw_payload == {"from_number": _NUMBER, "body": "hello"}


def test_simulator_normalize_sets_received_at():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert event.received_at is not None


def test_simulator_normalize_generates_unique_event_ids():
    e1 = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    e2 = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    assert e1.event_id != e2.event_id


# ── Twilio channel — unit tests ───────────────────────────────────────────────

def test_twilio_normalize_sets_sms_inbound_source():
    event = twilio_channel.normalize(
        from_number=_NUMBER, body="hello", raw_payload={"From": _NUMBER, "Body": "hello"}
    )
    assert event.source == EventSource.sms_inbound


def test_twilio_normalize_extracts_from_number():
    event = twilio_channel.normalize(
        from_number=_NUMBER, body="hi", raw_payload={"From": _NUMBER}
    )
    assert event.user_id == _NUMBER


def test_twilio_normalize_extracts_body():
    event = twilio_channel.normalize(
        from_number=_NUMBER, body="book me a flight", raw_payload={}
    )
    assert event.body == "book me a flight"


def test_twilio_normalize_preserves_raw_payload():
    raw = {"From": _NUMBER, "Body": "hi", "MessageSid": "SMxxx"}
    event = twilio_channel.normalize(from_number=_NUMBER, body="hi", raw_payload=raw)
    assert event.raw_payload["MessageSid"] == "SMxxx"


# ── Event Gateway — unit tests ────────────────────────────────────────────────

async def test_event_gateway_returns_string_reply():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    reply = await event_gateway.handle(event)
    assert isinstance(reply, str)
    assert len(reply) > 0


async def test_event_gateway_logs_internal_event_received():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    await event_gateway.handle(event)
    log_types = [e.event_type for e in events.get_log()]
    assert "internal_event_received" in log_types


async def test_event_gateway_logs_correct_source():
    event = simulator_channel.normalize(from_number=_NUMBER, body="hello")
    await event_gateway.handle(event)
    gateway_events = [
        e for e in events.get_log() if e.event_type == "internal_event_received"
    ]
    assert gateway_events[0].metadata["source"] == EventSource.simulate_inbound


async def test_event_gateway_handles_sms_inbound_event():
    """Gateway must handle events from any source, not just simulate_inbound."""
    event = twilio_channel.normalize(
        from_number=_NUMBER, body="hotel in Rome", raw_payload={"From": _NUMBER, "Body": "hotel in Rome"}
    )
    reply = await event_gateway.handle(event)
    assert isinstance(reply, str)
    assert len(reply) > 0
