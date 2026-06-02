"""luna/confirmation/schemas.py — PendingConfirmation schema."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from luna.agent.schemas import RiskLevel


class ConfirmationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    expired = "expired"


class PendingConfirmation(BaseModel):
    confirmation_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    task_id: str
    action_type: str
    human_summary: str
    structured_payload: dict = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.medium
    created_at: datetime
    expires_at: datetime
    status: ConfirmationStatus = ConfirmationStatus.pending
