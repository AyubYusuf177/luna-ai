"""
luna/gateway/event_gateway.py — Event Gateway.

The single bridge between all channel adapters and the Agent Runtime.

Every InternalEvent — regardless of source (SMS, /simulate, scheduler) —
passes through handle(). Nothing upstream knows about the runtime.
Nothing downstream knows about the channel.

v0.0.3: routes all events to the existing orchestrator stub.
v0.0.4: routes to the Agent Runtime (replace the import below).
"""

from luna.events import logger as events
from luna.gateway.schemas import InternalEvent
from luna.orchestrator.orchestrator import process


def handle(event: InternalEvent) -> str:
    """
    Receive an InternalEvent and return Luna's reply as a plain string.

    Logs internal_event_received so downstream tests and the audit log
    can confirm events are flowing through the gateway correctly.
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

    # v0.0.4: replace this call with agent_runtime.handle(event)
    body = event.body or ""
    return process(from_number=event.user_id, body=body)
