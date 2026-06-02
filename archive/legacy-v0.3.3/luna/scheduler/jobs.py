"""
luna/scheduler/jobs.py — Scheduler helpers (v0.0.8).

create_scheduler_event  Build a scheduler_tick InternalEvent for proactive sends.
build_message           Format a raw message string with a trigger-type prefix.
"""

from __future__ import annotations

from datetime import datetime, timezone

from luna.gateway.schemas import EventSource, InternalEvent
from luna.scheduler.schemas import TriggerType

_PREFIXES: dict[TriggerType, str] = {
    TriggerType.price_drop: "Price drop",
    TriggerType.check_in_reminder: "Check-in reminder",
    TriggerType.weather_change: "Weather heads-up",
    TriggerType.task_follow_up: "Quick follow-up",
}


def build_message(trigger_type: TriggerType, message: str) -> str:
    """Prepend a human-readable prefix to a proactive message body."""
    prefix = _PREFIXES.get(trigger_type, "Update")
    return f"{prefix}: {message}"


def create_scheduler_event(user_id: str, body: str) -> InternalEvent:
    """Wrap a proactive message body in a scheduler_tick InternalEvent."""
    return InternalEvent(
        source=EventSource.scheduler_tick,
        user_id=user_id,
        body=body,
        raw_payload={},
        received_at=datetime.now(timezone.utc),
    )
