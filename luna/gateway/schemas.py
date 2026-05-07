"""
luna/gateway/schemas.py — Gateway-level schemas.

InternalEvent is the single normalized event object that every channel
produces and the Agent Runtime consumes. Nothing downstream of the Event
Gateway ever sees a raw Twilio payload or a raw simulator dict.

SimulateRequest / SimulateResponse are the public HTTP API schemas for
the /simulate endpoint. They live here because they cross the HTTP boundary
(request in, response out) rather than being a channel-internal detail.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    simulate_inbound = "simulate_inbound"
    sms_inbound = "sms_inbound"
    scheduler_tick = "scheduler_tick"
    webhook_event = "webhook_event"


class InternalEvent(BaseModel):
    """
    Normalized event object produced by every channel adapter.

    The Agent Runtime (v0.0.4+) and Event Gateway operate on this schema
    exclusively. Source channel is recorded but never used for branching
    logic inside the runtime — events are source-agnostic.
    """

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    source: EventSource
    user_id: str          # E.164 phone number, or "system" for scheduler events
    body: str | None      # Message text. None for non-message events (scheduler ticks).
    raw_payload: dict     # Original source payload, kept for debugging and audit.
    received_at: datetime


# ── HTTP API schemas for /simulate ────────────────────────────────────────────

class SimulateRequest(BaseModel):
    from_number: str   # E.164, e.g. "+447700000000"
    body: str


class SimulateResponse(BaseModel):
    from_number: str
    reply: str
