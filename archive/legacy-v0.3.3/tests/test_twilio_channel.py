"""
Tests for the Twilio channel adapter and /twilio/sms webhook — v0.0.3.

Real Twilio API calls never happen in these tests because:
  TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are empty strings by default.
  send_reply() returns immediately when either credential is absent.
  signature_is_valid() returns False when TWILIO_AUTH_TOKEN is absent.

TWILIO_VALIDATE_SIGNATURES defaults to False, so most tests require no
signature header and receive 200 without any credential setup.
"""

import pytest
from httpx import ASGITransport, AsyncClient

import luna.config as config_module
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory

_NUMBER = "+447700000000"
_FORM = {"From": _NUMBER, "Body": "hello", "MessageSid": "SM123"}


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_twilio_webhook_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_twilio_webhook_missing_from_returns_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data={"Body": "hello"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_twilio_webhook_creates_user_in_memory():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/twilio/sms", data=_FORM)
    assert memory.get_user(_NUMBER) is not None


@pytest.mark.asyncio
async def test_twilio_webhook_stores_conversation_turns():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/twilio/sms", data=_FORM)
    turns = memory.get_conversation(_NUMBER)
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[0].body == "hello"
    assert turns[1].role == "luna"


# ── Payload normalization ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_twilio_webhook_logs_sms_inbound_source():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/twilio/sms", data=_FORM)
    gateway_events = [
        e for e in events.get_log() if e.event_type == "internal_event_received"
    ]
    assert len(gateway_events) == 1
    assert gateway_events[0].metadata["source"] == "sms_inbound"


@pytest.mark.asyncio
async def test_twilio_webhook_extracts_body_correctly():
    form = {"From": _NUMBER, "Body": "find me flights to Rome"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/twilio/sms", data=form)
    turns = memory.get_conversation(_NUMBER)
    assert turns[0].body == "find me flights to Rome"


# ── Signature validation ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_signature_validation_disabled_by_default():
    """With TWILIO_VALIDATE_SIGNATURES=false (default), no signature needed."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No X-Twilio-Signature header sent — must still return 200
        response = await client.post("/twilio/sms", data=_FORM)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_signature_rejected_when_validation_enabled(monkeypatch):
    """
    When TWILIO_VALIDATE_SIGNATURES=true and the signature is absent/invalid,
    the endpoint must return 403.

    Because TWILIO_AUTH_TOKEN is empty in tests, signature_is_valid() returns
    False for any request — no real Twilio validator is invoked.
    """
    monkeypatch.setattr(config_module.settings, "twilio_validate_signatures", True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
        # No X-Twilio-Signature → invalid → 403
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_validation_re_enabled_after_monkeypatch(monkeypatch):
    """Confirm monkeypatch isolation: default setting is restored after each test."""
    assert config_module.settings.twilio_validate_signatures is False


# ── TwiML response ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_twilio_webhook_returns_xml_content_type():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    assert "xml" in response.headers["content-type"].lower()


@pytest.mark.asyncio
async def test_twilio_webhook_response_contains_twiml_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    assert "<Response>" in response.text


@pytest.mark.asyncio
async def test_twilio_webhook_response_contains_message_tag():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    assert "<Message>" in response.text


@pytest.mark.asyncio
async def test_twilio_webhook_twiml_contains_reply_text():
    form = {"From": _NUMBER, "Body": "weather in Rome"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=form)
    assert "Rome" in response.text or "weather" in response.text.lower()


@pytest.mark.asyncio
async def test_twilio_webhook_twiml_is_parseable_xml():
    import xml.etree.ElementTree as ET

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    root = ET.fromstring(response.text)
    assert root.tag == "Response"
    assert root.find("Message") is not None


@pytest.mark.asyncio
async def test_twilio_webhook_twiml_message_is_non_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.text)
    assert len(root.find("Message").text) > 0


# ── No real API calls ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_twilio_api_calls_without_credentials():
    """
    With TwiML responses, the reply is delivered by Twilio via the response
    body — no outbound API credentials are needed for the basic SMS loop.
    The test completing without error proves no real API call was attempted.
    """
    assert config_module.settings.twilio_account_sid == ""
    assert config_module.settings.twilio_auth_token == ""

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/twilio/sms", data=_FORM)

    assert response.status_code == 200  # completed without any API error


# ── format_response() unit tests ──────────────────────────────────────────────

def test_format_response_content_type_is_xml():
    from luna.channels.twilio import format_response
    response = format_response("hello")
    assert "xml" in response.media_type.lower()


def test_format_response_contains_response_tag():
    from luna.channels.twilio import format_response
    assert b"<Response>" in format_response("hello").body


def test_format_response_contains_message_tag():
    from luna.channels.twilio import format_response
    assert b"<Message>" in format_response("hello").body


def test_format_response_escapes_special_characters():
    from luna.channels.twilio import format_response
    body = format_response("<test> & 'quote'").body
    assert b"<test>" not in body
    assert b"&amp;" in body
    assert b"&lt;" in body
