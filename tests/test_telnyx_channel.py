"""
tests/test_telnyx_channel.py — Telnyx channel adapter and /telnyx/sms webhook tests.

Real Telnyx API calls never happen in these tests because:
  TELNYX_API_KEY is empty by default (reset by _safe_settings in conftest).
  send_reply() returns immediately when telnyx_api_key is empty.
  _send_telnyx_message is monkeypatched where outbound behaviour is verified.
"""

import pytest
from httpx import ASGITransport, AsyncClient

import luna.channels.telnyx as telnyx_module
import luna.config as config_module
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory

_NUMBER = "+447700000001"

_VALID_PAYLOAD = {
    "data": {
        "event_type": "message.received",
        "payload": {
            "from": {"phone_number": _NUMBER},
            "to": [{"phone_number": "+16284321017"}],
            "text": "hello",
        },
    }
}

_NON_MESSAGE_PAYLOAD = {
    "data": {
        "event_type": "message.sent",
        "payload": {},
    }
}


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telnyx_webhook_returns_200_for_valid_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_telnyx_webhook_missing_from_returns_400():
    payload = {
        "data": {
            "event_type": "message.received",
            "payload": {"from": {}, "text": "hello"},
        }
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_telnyx_non_message_event_returns_200_without_processing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=_NON_MESSAGE_PAYLOAD)
    assert response.status_code == 200
    assert memory.get_user(_NUMBER) is None


# ── Payload normalization ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telnyx_webhook_creates_user_in_memory():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert memory.get_user(_NUMBER) is not None


@pytest.mark.asyncio
async def test_telnyx_webhook_stores_conversation_turns():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    turns = memory.get_conversation(_NUMBER)
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[0].body == "hello"
    assert turns[1].role == "luna"


@pytest.mark.asyncio
async def test_telnyx_webhook_logs_sms_inbound_source():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    gateway_events = [
        e for e in events.get_log() if e.event_type == "internal_event_received"
    ]
    assert len(gateway_events) == 1
    assert gateway_events[0].metadata["source"] == "sms_inbound"


@pytest.mark.asyncio
async def test_telnyx_webhook_extracts_body_correctly():
    payload = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {"phone_number": _NUMBER},
                "to": [{"phone_number": "+16284321017"}],
                "text": "find me flights to Rome",
            },
        }
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=payload)
    turns = memory.get_conversation(_NUMBER)
    assert turns[0].body == "find me flights to Rome"


# ── Response format ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telnyx_webhook_response_content_type_is_json():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_telnyx_webhook_response_body_is_empty_object():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert response.json() == {}


# ── Outbound send ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_telnyx_send_reply_not_called_without_api_key(monkeypatch):
    calls: list = []

    async def _mock_send(api_key, from_number, to, text):
        calls.append((to, text))

    monkeypatch.setattr(telnyx_module, "_send_telnyx_message", _mock_send)
    # telnyx_api_key is "" by default from _safe_settings in conftest
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert calls == []


@pytest.mark.asyncio
async def test_telnyx_send_reply_called_with_correct_args(monkeypatch):
    calls: list = []

    async def _mock_send(api_key, from_number, to, text):
        calls.append({"to": to, "text": text, "api_key": api_key})

    monkeypatch.setattr(telnyx_module, "_send_telnyx_message", _mock_send)
    monkeypatch.setattr(config_module.settings, "telnyx_api_key", "test-key")
    monkeypatch.setattr(config_module.settings, "telnyx_phone_number", "+16284321017")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/telnyx/sms", json=_VALID_PAYLOAD)

    assert len(calls) == 1
    assert calls[0]["to"] == _NUMBER
    assert calls[0]["api_key"] == "test-key"


# ── No real API calls ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_real_telnyx_api_calls_without_credentials():
    assert config_module.settings.telnyx_api_key == ""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/telnyx/sms", json=_VALID_PAYLOAD)
    assert response.status_code == 200
