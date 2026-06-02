"""
luna/channels/telnyx.py — Telnyx SMS channel adapter.

Responsibilities:
  parse_request()         Extract and normalize an inbound Telnyx webhook.
  send_reply()            Send outbound SMS via the Telnyx Messages API.
  _send_telnyx_message()  Module-level httpx helper — monkeypatchable in tests.

Telnyx webhook differences from Twilio:
  - Payload is JSON, not form-encoded.
  - Multiple event types arrive at the same URL; only message.received is processed.
  - There is no TwiML equivalent — replies are sent via a separate API call.
  - The HTTP response to Telnyx is always 200 {}.

send_reply() is a no-op when TELNYX_API_KEY is not configured — no real API
calls are made during tests or local dev without an explicit key.
"""

from datetime import datetime, timezone

import httpx
from fastapi import Request

from luna.config import settings
from luna.gateway.schemas import EventSource, InternalEvent

_TELNYX_MESSAGES_URL = "https://api.telnyx.com/v2/messages"


async def parse_request(
    request: Request,
) -> tuple[InternalEvent | None, dict | None]:
    """
    Parse an inbound Telnyx webhook request.

    Returns (InternalEvent, None) for message.received events.
    Returns (None, None) for other event types — caller should return 200 {} immediately.
    Returns (None, error_dict) for malformed payloads.
    """
    try:
        body = await request.json()
    except Exception:
        return None, {"status_code": 400, "detail": "Invalid JSON in Telnyx webhook"}

    data = body.get("data", {})
    event_type = data.get("event_type", "")

    if event_type != "message.received":
        return None, None  # not an inbound message — ack and ignore

    payload = data.get("payload", {})
    from_number = payload.get("from", {}).get("phone_number", "")
    text = payload.get("text", "")

    if not from_number:
        return None, {"status_code": 400, "detail": "Missing from.phone_number in Telnyx payload"}

    return _normalize(from_number=from_number, body=text, raw_payload=body), None


def _normalize(from_number: str, body: str, raw_payload: dict) -> InternalEvent:
    """Build an InternalEvent from a parsed Telnyx inbound payload."""
    return InternalEvent(
        source=EventSource.sms_inbound,
        user_id=from_number,
        body=body,
        raw_payload=raw_payload,
        received_at=datetime.now(timezone.utc),
    )


async def _send_telnyx_message(api_key: str, from_number: str, to: str, text: str) -> None:
    """
    POST to Telnyx /v2/messages via httpx.

    Module-level so tests can monkeypatch without touching httpx internals:
      monkeypatch.setattr(telnyx_module, "_send_telnyx_message", mock_fn)
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            _TELNYX_MESSAGES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"from": from_number, "to": to, "text": text},
        )


async def send_reply(to: str, body: str) -> None:
    """
    Send an outbound SMS via the Telnyx Messages API.

    No-op when TELNYX_API_KEY is empty — guarantees no real API calls
    during tests or local dev without an explicit key.
    """
    if not settings.telnyx_api_key:
        return
    await _send_telnyx_message(
        api_key=settings.telnyx_api_key,
        from_number=settings.telnyx_phone_number,
        to=to,
        text=body,
    )
