"""luna/policy/schemas.py — PolicyDecision schema."""

from pydantic import BaseModel

from luna.agent.schemas import RiskLevel


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str | None = None
    risk_level: RiskLevel = RiskLevel.low
    requires_confirmation: bool = False
    rewritten_reply: str | None = None
    command: str | None = None  # "stop" | "start" when a channel command is detected
