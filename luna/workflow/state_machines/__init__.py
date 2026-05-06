"""
workflow.state_machines — One module per workflow type.

Each state machine defines:
- Valid states (as string constants or an enum).
- Allowed transitions (from_state → to_state, with trigger condition).
- Required fields that must be collected before advancing past COLLECTING states.
- Completion criteria (conditions that mark the workflow COMPLETED).
- Failure states and what triggers them.

Modules (implemented from v0.0.4 onwards):
    onboarding.py
    flight_search.py
    hotel_search.py
    price_alert.py
    itinerary_management.py
    booking_handoff.py
"""
