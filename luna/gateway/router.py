"""
luna/gateway/router.py — HTTP routes for all channel adapters.

v0.0.3 routes:
  POST /simulate      Local dev/test simulator. No Twilio required.
  POST /twilio/sms    Twilio inbound SMS webhook.

Both routes follow the same pattern:
  1. Read raw payload from the channel.
  2. Normalize to InternalEvent via the appropriate channel adapter.
  3. Pass InternalEvent to the Event Gateway.
  4. Return the reply (or 200 for Twilio, which replies out-of-band).

Channel adapters and the Event Gateway contain all logic.
This router stays thin.
"""

from fastapi import APIRouter, HTTPException, Request, Response

from luna.channels import simulator as simulator_channel
from luna.channels import telnyx as telnyx_channel
from luna.channels import twilio as twilio_channel
from luna.events import logger as events
from luna.gateway import event_gateway
from luna.gateway.schemas import (
    SimulateProactiveRequest,
    SimulateProactiveResponse,
    SimulateRequest,
    SimulateResponse,
)
from luna.scheduler import jobs as scheduler_jobs
from luna.scheduler import proactive_engine
from luna.scheduler.schemas import ProactiveCandidate, ProactiveDecisionType, TriggerType

router = APIRouter()


# ── /simulate — local SMS simulator ──────────────────────────────────────────

@router.post("/simulate", response_model=SimulateResponse, tags=["dev"])
async def simulate(request: SimulateRequest) -> SimulateResponse:
    """
    Local SMS simulator for development and testing.

    Accepts JSON, produces an InternalEvent, routes through the Event
    Gateway, and returns Luna's reply synchronously. No Twilio account
    or internet connection required.
    """
    event = simulator_channel.normalize(
        from_number=request.from_number,
        body=request.body,
    )
    reply = await event_gateway.handle(event)
    return SimulateResponse(from_number=request.from_number, reply=reply)


# ── /simulate/proactive — Proactive engine test harness ───────────────────────

@router.post("/simulate/proactive", response_model=SimulateProactiveResponse, tags=["dev"])
async def simulate_proactive(request: SimulateProactiveRequest) -> SimulateProactiveResponse:
    """
    Proactive engine simulator for development and testing.

    Builds a ProactiveCandidate from the request, runs it through the
    decision gate, and returns the decision without requiring a real
    scheduler or APScheduler to be running.
    """
    trigger_type = TriggerType(request.trigger_type)
    formatted_message = scheduler_jobs.build_message(trigger_type, request.message)

    candidate = ProactiveCandidate(
        user_id=request.user_id,
        trigger_type=trigger_type,
        message=formatted_message,
        proactive_opt_in=request.proactive_opt_in,
        opted_out=request.opted_out,
        send_window_start=request.send_window_start,
        send_window_end=request.send_window_end,
    )

    decision = proactive_engine.evaluate(candidate)

    if decision.decision == ProactiveDecisionType.send:
        events.log("proactive_sent", request.user_id, {
            "trigger_type": request.trigger_type,
            "message": formatted_message,
        })

    return SimulateProactiveResponse(
        decision=decision.decision,
        reason=decision.reason,
        message=decision.message,
        retry_at=decision.retry_at,
    )


# ── /twilio/sms — Twilio inbound SMS webhook ──────────────────────────────────

@router.post("/twilio/sms", tags=["channels"])
async def twilio_sms_webhook(request: Request) -> Response:
    """
    Twilio inbound SMS webhook.

    Delegates all Twilio-specific concerns (field extraction, signature
    validation, TwiML formatting) to the Twilio channel adapter.
    Point ngrok at this endpoint for real SMS testing:
      POST https://<ngrok-id>.ngrok-free.app/twilio/sms
    """
    event, err = await twilio_channel.parse_request(request)
    if err:
        raise HTTPException(**err)
    reply = await event_gateway.handle(event)
    return twilio_channel.format_response(reply)


# ── /telnyx/sms — Telnyx inbound SMS webhook ──────────────────────────────────

@router.post("/telnyx/sms", tags=["channels"])
async def telnyx_sms_webhook(request: Request) -> Response:
    """
    Telnyx inbound SMS webhook.

    Telnyx sends a JSON POST. Non-message events are acknowledged and ignored.
    Replies are sent via the Telnyx Messages API (no TwiML equivalent).
    Point ngrok at this endpoint for Telnyx SMS testing:
      POST https://<ngrok-id>.ngrok-free.app/telnyx/sms
    """
    event, err = await telnyx_channel.parse_request(request)
    if err:
        raise HTTPException(**err)
    if event is None:  # non-message.received event — ack and ignore
        return Response(content='{}', media_type='application/json')
    reply = await event_gateway.handle(event)
    await telnyx_channel.send_reply(to=event.user_id, body=reply)
    return Response(content='{}', media_type='application/json')
