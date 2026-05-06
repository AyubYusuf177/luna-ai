"""
Pydantic schema for the event log — v0.0.2 subset.

Full event type enum (all types logged from v0.0.2 onwards) is
documented in luna/events/__init__.py. Only the entry schema lives here.
"""

from datetime import datetime

from pydantic import BaseModel


class EventLogEntry(BaseModel):
    event_id: str       # UUID string
    user_id: str        # E.164 phone number
    event_type: str     # e.g. "inbound_sms_received"
    timestamp: datetime
    metadata: dict      # event-specific payload
