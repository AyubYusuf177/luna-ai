"""
In-memory event logger — v0.0.2.

Append-only. Nothing is ever updated or deleted from the log.
Module-level list acts as the store for v0.1; a persistent backend
will be added in a later milestone behind the same interface.

Public interface:
    log(event_type, user_id, metadata)  → EventLogEntry
    get_log()                           → list[EventLogEntry]
    reset()                             → None  [tests only]
"""

from datetime import datetime, timezone
from uuid import uuid4

from luna.events.schemas import EventLogEntry

# ── Store state ───────────────────────────────────────────────────────────────

_log: list[EventLogEntry] = []


# ── Write ─────────────────────────────────────────────────────────────────────

def log(event_type: str, user_id: str, metadata: dict | None = None) -> EventLogEntry:
    """Append one event to the log and return it."""
    entry = EventLogEntry(
        event_id=str(uuid4()),
        user_id=user_id,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        metadata=metadata or {},
    )
    _log.append(entry)
    return entry


# ── Read ──────────────────────────────────────────────────────────────────────

def get_log() -> list[EventLogEntry]:
    """Return a copy of the full event log."""
    return list(_log)


# ── Test utility ──────────────────────────────────────────────────────────────

def reset() -> None:
    """Clear all events. Call from test fixtures only."""
    _log.clear()
