"""
Gateway router — v0.0.2: local SMS simulator only.

POST /simulate lets developers test the full message loop without
Twilio or an internet connection. It accepts a from_number and body,
runs the orchestrator, and returns Luna's reply.

In v0.0.3 this router will gain:
- POST /webhook/twilio  — real Twilio inbound SMS handler
- Twilio signature validation middleware
- Async processing (200 returned immediately, reply sent out-of-band)
"""

from fastapi import APIRouter

from luna.gateway.schemas import SimulateRequest, SimulateResponse
from luna.orchestrator.orchestrator import process

router = APIRouter()


@router.post("/simulate", response_model=SimulateResponse, tags=["dev"])
async def simulate(request: SimulateRequest) -> SimulateResponse:
    """
    Local SMS simulator. No Twilio account or internet required.

    Mimics the inbound SMS path:
    receive message → run orchestrator → return Luna's reply.
    """
    reply = process(from_number=request.from_number, body=request.body)
    return SimulateResponse(from_number=request.from_number, reply=reply)
