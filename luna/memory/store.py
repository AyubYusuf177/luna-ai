"""
In-memory store — v0.0.2.

Module-level dicts act as the store. All state is lost on server
restart; that is acceptable in v0.1. A persistent backend (SQLite →
PostgreSQL) will be swapped in behind the same interface in a later
milestone without changing any caller code.

Public interface used by the orchestrator:
    get_user(user_id)           → UserProfile | None
    create_user(user_id)        → UserProfile
    get_conversation(user_id)   → list[ConversationTurn]
    append_turn(user_id, role, body) → ConversationTurn
    reset()                     → None  [tests only]
"""

from datetime import datetime, timezone

from luna.memory.schemas import ConversationTurn, UserProfile

# ── Store state ───────────────────────────────────────────────────────────────

_users: dict[str, UserProfile] = {}
_conversations: dict[str, list[ConversationTurn]] = {}


# ── User profile ──────────────────────────────────────────────────────────────

def get_user(user_id: str) -> UserProfile | None:
    """Return the stored profile for user_id, or None if not found."""
    return _users.get(user_id)


def create_user(user_id: str) -> UserProfile:
    """Create and store a new UserProfile keyed by user_id (phone number)."""
    profile = UserProfile(user_id=user_id, created_at=datetime.now(timezone.utc))
    _users[user_id] = profile
    return profile


# ── Conversation memory ───────────────────────────────────────────────────────

def get_conversation(user_id: str) -> list[ConversationTurn]:
    """Return all stored conversation turns for user_id."""
    return _conversations.get(user_id, [])


def append_turn(user_id: str, role: str, body: str) -> ConversationTurn:
    """Append one turn to the conversation history and return it."""
    turn = ConversationTurn(role=role, body=body, timestamp=datetime.now(timezone.utc))
    if user_id not in _conversations:
        _conversations[user_id] = []
    _conversations[user_id].append(turn)
    return turn


# ── Test utility ──────────────────────────────────────────────────────────────

def reset() -> None:
    """Clear all store state. Call from test fixtures only."""
    _users.clear()
    _conversations.clear()
