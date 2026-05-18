"""
luna/gateway/event_gateway.py — Event Gateway.

The single bridge between all channel adapters and the Agent Runtime.

Every InternalEvent — regardless of source (SMS, /simulate, scheduler) —
passes through handle(). Nothing upstream knows about the runtime.
Nothing downstream knows about the channel.

v0.0.3: routed to the orchestrator stub.
v0.0.4: routes to the Agent Runtime.
"""

from luna.agent import runtime as agent_runtime
from luna.events import logger as events
from luna.gateway.schemas import InternalEvent


async def handle(event: InternalEvent) -> str:
    """
    Receive an InternalEvent and return Luna's reply as a plain string.

    Logs internal_event_received so the audit log can confirm events are
    flowing through the gateway. All further processing is in the runtime.
    """
    events.log(
        "internal_event_received",
        event.user_id,
        {
            "event_id": event.event_id,
            "source": event.source,
            "body_length": len(event.body) if event.body else 0,
        },
    )

    return await agent_runtime.handle(event)
