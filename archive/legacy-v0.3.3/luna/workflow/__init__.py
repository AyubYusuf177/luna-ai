"""
workflow — Workflow engine and state machines.

Responsibilities (implemented from v0.0.4):
- Maintain persistent Workflow objects (id, type, goal, current_state,
  known_fields, missing_fields, next_action, status, timestamps).
- Run state machines for each workflow type:
    onboarding, flight_search, hotel_search, price_alert,
    itinerary_management, booking_handoff.
- Validate all state transitions against each machine's allowed rules.
- Identify which required fields are known vs missing after each turn.
- Detect workflow completion and trigger archival to Travel Memory.
- Route inbound messages to the correct active workflow when a user
  has multiple workflows running simultaneously.

The Workflow Engine is Luna's core differentiator. It holds goals across
time. It does not just classify messages — it manages goal lifecycles.
"""
