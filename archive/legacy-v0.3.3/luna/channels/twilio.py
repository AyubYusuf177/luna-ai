"""
luna/channels/twilio.py — Twilio SMS channel adapter.

Responsibilities:
  parse_request()       Extract, validate, and normalize an inbound webhook Request.
  format_response()     Build a TwiML Response for Twilio to deliver.
  normalize()           Convert raw Twilio form fields → InternalEvent.
  signature_is_valid()  Validate X-Twilio-Signature header (HMAC-SHA1).
  send_reply()          Send an outbound SMS via the Twilio Messages API.

All functions are pure channel concerns. No Luna business logic here.

send_reply() is a no-op when TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN are
not configured — this keeps tests and local dev free of real API calls
with no mocking required.
"""

import asyncio
from datetime import datetime, timezone
from xml.sax.saxutils import escape as _xml_escape

from fastapi import Request, Response

from luna.config import settings
from luna.gateway.schemas import EventSource, InternalEvent


async def parse_request(
    request: Request,
) -> tuple[InternalEvent | None, dict | None]:
    """
    Extract, validate, and normalize an inbound Twilio webhook request.

    Returns (InternalEvent, None) on success.
    Returns (None, error_dict) on failure — the dict unpacks directly into
    HTTPException(**err) at the call site.
    """
    form_data = dict(await request.form())
    from_number = form_data.get("From", "")
    body = form_data.get("Body", "")

    if not from_number:
        return None, {"status_code": 400, "detail": "Missing 'From' field in Twilio payload"}

    if settings.twilio_validate_signatures:
        signature = request.headers.get("X-Twilio-Signature", "")
        if not signature_is_valid(str(request.url), form_data, signature):
            return None, {"status_code": 403, "detail": "Invalid Twilio signature"}

    return normalize(from_number=from_number, body=body, raw_payload=form_data), None


def format_response(reply: str) -> Response:
    """Build a TwiML Response for Twilio to deliver to the user."""
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{_xml_escape(reply)}</Message></Response>"
    )
    return Response(content=twiml, media_type="text/xml; charset=utf-8")


def normalize(from_number: str, body: str, raw_payload: dict) -> InternalEvent:
    """Build an InternalEvent from a Twilio webhook payload."""
    return InternalEvent(
        source=EventSource.sms_inbound,
        user_id=from_number,
        body=body,
        raw_payload=raw_payload,
        received_at=datetime.now(timezone.utc),
    )


def signature_is_valid(request_url: str, form_params: dict, signature: str) -> bool:
    """
    Validate the X-Twilio-Signature header against the request URL and body.

    Returns False (not True) when TWILIO_AUTH_TOKEN is not configured.
    This means an unconfigured server with validation enabled will reject
    all requests — a safe default that prevents accidental open endpoints.
    """
    if not settings.twilio_auth_token:
        return False

    from twilio.request_validator import RequestValidator  # lazy import

    validator = RequestValidator(settings.twilio_auth_token)
    return validator.validate(request_url, form_params, signature)


async def send_reply(to: str, body: str) -> None:
    """
    Send an outbound SMS via the Twilio REST API.

    No-op when TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN are empty.
    This guarantees no real API calls occur during tests or local dev
    without any mocking required.

    The Twilio REST client is synchronous; it runs in a thread to avoid
    blocking the FastAPI event loop.
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        return

    def _call_twilio() -> None:
        from twilio.rest import Client  # lazy import

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=settings.twilio_phone_number,
            to=to,
        )

    await asyncio.to_thread(_call_twilio)
