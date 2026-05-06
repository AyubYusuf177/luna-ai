"""
Pydantic schemas for the SMS gateway layer.

SimulateRequest / SimulateResponse are used by the local /simulate
endpoint (v0.0.2). In v0.0.3 these will be joined by TwilioInboundSMS
and TwilioOutboundSMS schemas when the real webhook is wired up.
"""

from pydantic import BaseModel


class SimulateRequest(BaseModel):
    from_number: str  # E.164 format, e.g. "+447700000000"
    body: str


class SimulateResponse(BaseModel):
    from_number: str
    reply: str
