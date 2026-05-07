"""
luna/events/logger.py — Append-only event logger.

All calls delegate to the active backend (in-memory or SQLite).

Public interface (unchanged from v0.0.2):
    log(event_type, user_id, metadata)  → EventLogEntry
    get_log()                           → list[EventLogEntry]
    reset()                             → None  [tests only]
"""

from luna.events.schemas import EventLogEntry
from luna.memory.backend import get_backend


def log(event_type: str, user_id: str, metadata: dict | None = None) -> EventLogEntry:
    return get_backend().log_event(event_type, user_id, metadata or {})


def get_log() -> list[EventLogEntry]:
    return get_backend().get_event_log()


def reset() -> None:
    """Clear the event log only. Does not affect users, conversations, or tasks."""
    get_backend().reset_events()
