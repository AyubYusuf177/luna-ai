"""
luna/channels/simulator.py — Simulator channel adapter.

Converts a local /simulate HTTP request into an InternalEvent.
No external calls. No business logic. Pure normalization.

Used exclusively in development and testing.
"""

from datetime import datetime, timezone

from luna.gateway.schemas import EventSource, InternalEvent


def normalize(from_number: str, body: str) -> InternalEvent:
    """
    Build an InternalEvent from a simulator request payload.

    Source is always EventSource.simulate_inbound so the Event Gateway
    and Agent Runtime can log the origin if needed.
    """
    raw = {"from_number": from_number, "body": body}
    return InternalEvent(
        source=EventSource.simulate_inbound,
        user_id=from_number,
        body=body,
        raw_payload=raw,
        received_at=datetime.now(timezone.utc),
    )
