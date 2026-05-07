"""
luna/memory/store.py — User profile and conversation memory.

All calls delegate to the active backend (in-memory or SQLite).
The backend is selected at startup via luna/memory/backend.py.

Public interface (unchanged from v0.0.2):
    get_user(user_id)               → UserProfile | None
    create_user(user_id)            → UserProfile
    get_conversation(user_id)       → list[ConversationTurn]
    append_turn(user_id, role, body) → ConversationTurn
    reset()                         → None  [tests only]
"""

from luna.memory.backend import get_backend
from luna.memory.schemas import ConversationTurn, UserProfile


def get_user(user_id: str) -> UserProfile | None:
    return get_backend().get_user(user_id)


def create_user(user_id: str) -> UserProfile:
    return get_backend().create_user(user_id)


def get_conversation(user_id: str) -> list[ConversationTurn]:
    return get_backend().get_conversation(user_id)


def append_turn(user_id: str, role: str, body: str) -> ConversationTurn:
    return get_backend().append_turn(user_id, role, body)


def reset() -> None:
    """Clear users and conversations. Does not clear tasks or events."""
    b = get_backend()
    b.reset_users()
    b.reset_conversations()
