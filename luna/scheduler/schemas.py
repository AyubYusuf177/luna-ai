"""
luna/scheduler/schemas.py — Proactive engine schemas (v0.0.8).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TriggerType(str, Enum):
    price_drop = "price_drop"
    check_in_reminder = "check_in_reminder"
    weather_change = "weather_change"
    task_follow_up = "task_follow_up"


class ProactiveDecisionType(str, Enum):
    send = "send"
    defer = "defer"
    suppress = "suppress"


class ProactiveCandidate(BaseModel):
    user_id: str
    trigger_type: TriggerType
    message: str
    task_id: str | None = None
    proactive_opt_in: bool = True
    opted_out: bool = False
    send_window_start: int = 8   # hour 0–23, inclusive lower bound
    send_window_end: int = 21    # hour 0–23, exclusive upper bound


class ProactiveDecision(BaseModel):
    decision: ProactiveDecisionType
    reason: str
    user_id: str
    task_id: str | None = None
    message: str | None = None    # set only when decision == send
    retry_at: datetime | None = None  # set only when decision == defer
