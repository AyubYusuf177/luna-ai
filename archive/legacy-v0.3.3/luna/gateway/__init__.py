"""
gateway — Messaging interface layer.

Responsibilities (implemented from v0.0.3):
- Receive inbound SMS via Twilio webhook POST.
- Validate Twilio request signatures before processing anything.
- Normalize the raw Twilio payload into a clean InboundSMS schema.
- Return HTTP 200 to Twilio immediately (before any async processing).
- Send outbound SMS via the Twilio REST API.
- Expose a /simulate endpoint for local testing without Twilio.

This package is the only place that knows about Twilio. All other
packages receive and return internal schemas, not Twilio objects.
"""
