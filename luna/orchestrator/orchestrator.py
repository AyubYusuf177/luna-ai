"""
Orchestrator stub — v0.0.2.

Implements the first 6 steps of the full 11-step runtime loop using
deterministic placeholder logic (no LLM, no Twilio, no tools).

Full loop (steps 7–11 added in later milestones):
    1.  identify_user       ← implemented
    2.  load_memory         ← implemented (conversation turns)
    3.  route_workflow      ← v0.0.4
    4.  advance_state       ← v0.0.4
    5.  plan_next_step      ← v0.0.3 (LLM)
    6.  execute_action      ← v0.0.5
    7.  safety_check        ← v0.0.4
    8.  compose_response    ← v0.0.4
    9.  log_event           ← implemented
    10. persist_memory      ← implemented
    11. send_sms            ← v0.0.3 (Twilio)
"""

from luna.events import logger as events
from luna.memory import store as memory

# Deterministic placeholder reply used until Claude is wired in (v0.0.3).
_PLACEHOLDER_REPLY = (
    "Hi, I'm Luna. I'm being set up as your SMS-native travel assistant. "
    "What city do you usually fly from?"
)


def process(from_number: str, body: str) -> str:
    """
    Run the orchestrator loop for one inbound message.

    Returns Luna's reply as a plain string.
    """

    # Step 1 — Log inbound event
    events.log("inbound_sms_received", from_number, {"body": body})

    # Step 2 — Identify user; create profile if first contact
    user = memory.get_user(from_number)
    is_new_user = user is None
    if is_new_user:
        user = memory.create_user(from_number)
    events.log("user_identified", from_number, {"is_new_user": is_new_user})

    # Step 3 — Append inbound turn to conversation memory
    memory.append_turn(from_number, "user", body)

    # Step 4 — Generate reply
    # v0.0.2: deterministic placeholder. Replaced by LLM reasoning in v0.0.3.
    reply = _PLACEHOLDER_REPLY

    # Step 5 — Append outbound turn to conversation memory
    memory.append_turn(from_number, "luna", reply)

    # Step 6 — Log outbound event
    events.log("outbound_sms_sent", from_number, {"body": reply})

    return reply
