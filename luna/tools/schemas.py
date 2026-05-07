"""
luna/tools/schemas.py — Tool layer data contracts.

Three types:
  ToolDefinition  — static metadata registered in the registry.
  ToolRequest     — what the dispatcher receives (tool name + args from planner).
  ToolResult      — what every mock and real tool returns.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from luna.agent.schemas import RiskLevel


class ToolDefinition(BaseModel):
    name: str
    description: str
    risk_level: RiskLevel
    is_mock: bool = True
    enabled_in_v0: bool = True


class ToolRequest(BaseModel):
    tool_name: str
    args: dict = {}


class ToolStatus(str, Enum):
    ok = "ok"
    missing_args = "missing_args"
    error = "error"
    disabled = "disabled"


class ToolResult(BaseModel):
    tool_name: str
    status: ToolStatus
    data: dict = {}
    reply_text: str
