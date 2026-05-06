"""
Pydantic schemas for the memory layer — v0.0.2 subset.

Only the fields needed for the simulator are defined here.
Additional fields (travel_style, budget, preferences, etc.) will be
added to UserProfile during the onboarding milestone (v0.0.4).

Full six-segment memory model (all implemented in v0.0.4):
    UserProfile, ConversationMemory, WorkflowMemory,
    TravelMemory, ConsentMemory, EventLog
"""

from datetime import datetime

from pydantic import BaseModel


class UserProfile(BaseModel):
    """Stable facts about the user. Primary key is user_id (phone number)."""

    user_id: str        # E.164 phone number — permanent primary identifier
    created_at: datetime


class ConversationTurn(BaseModel):
    """A single message turn in the conversation history."""

    role: str           # "user" | "luna"
    body: str
    timestamp: datetime
