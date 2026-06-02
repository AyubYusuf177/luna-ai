"""
luna/channels — Channel adapters.

Each module in this package handles exactly one inbound source.
Channel adapters have one job: receive a raw payload from their source,
normalize it into an InternalEvent, and hand it to the Event Gateway.

They must not contain Luna business logic. No memory reads. No LLM calls.
No workflow logic. Pure I/O normalization only.

Modules:
    simulator.py  — /simulate HTTP endpoint adapter (dev/test)
    twilio.py     — Twilio SMS webhook adapter (production)

Future adapters (same interface, different source):
    whatsapp.py   — WhatsApp Business API
    email.py      — Inbound email (SendGrid / Postmark)
"""
