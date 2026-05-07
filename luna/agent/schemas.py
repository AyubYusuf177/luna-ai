"""
luna/agent/schemas.py — TravelTask and Planner schemas.

TravelTask is Luna's core unit of work. Every user goal — a flight
search, a hotel comparison, a price alert — is a TravelTask with a
lifecycle, not a loose chat message.

PlannerOutput is what the planner (fallback or Claude) returns on every
turn. The runtime merges it into the active TravelTask.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class TaskPattern(str, Enum):
    """
    How Luna intends to handle the user's goal.

    answer_with_context         — Goal can be answered directly (e.g. weather info).
    ask_clarification           — More information needed before acting.
    search_and_compare          — Search for options and present them (flights, hotels).
    monitor_and_alert           — Watch for a condition and notify (price drops).
    booking_handoff             — Hand the user off to a booking provider.
    modify_saved_trip           — Update an existing saved trip or itinerary.
    confirmation_required_action — Action is ready but needs explicit user YES/NO.
    """

    answer_with_context = "answer_with_context"
    ask_clarification = "ask_clarification"
    search_and_compare = "search_and_compare"
    monitor_and_alert = "monitor_and_alert"
    booking_handoff = "booking_handoff"
    modify_saved_trip = "modify_saved_trip"
    confirmation_required_action = "confirmation_required_action"


class TaskStatus(str, Enum):
    active = "active"
    pending_confirmation = "pending_confirmation"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ── TravelTask ────────────────────────────────────────────────────────────────

class TravelTask(BaseModel):
    """
    A persistent, goal-directed unit of work.

    Created when a user expresses a travel intent. Updated on every
    subsequent turn until the goal is reached or the task is cancelled.
    Unlike a chat message, a TravelTask survives across conversation turns.
    """

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    source: str                         # EventSource value that created this task
    goal: str                           # Natural language goal, e.g. "Flights LHR→TYO Oct"
    task_pattern: TaskPattern = TaskPattern.ask_clarification
    status: TaskStatus = TaskStatus.active
    known_fields: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    candidate_tools: list[str] = Field(default_factory=list)
    selected_tools: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.low
    next_action: str = "ask_clarification"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── PlannerOutput ─────────────────────────────────────────────────────────────

class PlannerOutput(BaseModel):
    """
    Structured output from the planner (fallback or Claude).

    The runtime merges these fields into the active TravelTask and uses
    reply_draft as the basis for the outbound SMS. reply_draft must
    never claim a booking was made unless the system actually made one.
    """

    goal: str
    task_pattern: TaskPattern
    known_fields: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    candidate_tools: list[str] = Field(default_factory=list)
    selected_tools: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.low
    next_action: str
    reply_draft: str
