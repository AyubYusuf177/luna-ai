"""
memory — User state persistence layer.

Responsibilities (implemented from v0.0.4):
- Provide a clean read/write interface for all six memory segments.
- v0.1 backend: in-memory Python dicts (keyed by user_id / phone number).
- Future backends: SQLite, then PostgreSQL (swap implementation, not interface).

Six memory segments:
    UserProfile     — stable facts: name, home city, travel style, preferences.
    ConversationMemory — rolling last-10-turns message history.
    WorkflowMemory  — all active and recently completed Workflow objects.
    TravelMemory    — past trips, active trips, saved searches, price alerts.
    ConsentMemory   — SMS opt-in status, proactive consent, STOP/START history.
    EventLog        — append-only record of all meaningful system events.

The phone number is the primary user identifier in v0.1.
All memory segments are keyed by user_id (= E.164 phone number string).
"""
