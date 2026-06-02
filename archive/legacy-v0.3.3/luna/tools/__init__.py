"""
tools — Tool abstraction layer and action registry.

Responsibilities (implemented from v0.0.5):
- Define the Action Registry: every action Luna can take, with its
  risk_level, requires_confirmation flag, tool_required, allowed_in_v0_1,
  and fallback_behavior.
- Dispatch structured intents to the correct tool implementation.
- Check allowed_in_v0_1 before executing any action.
- Use fallback_behavior if a tool is unavailable or fails.
- Return structured ToolResult objects (never raw API responses or SMS copy).

v0.1 mock tools (luna/tools/mock/):
    mock_flight_search      — fixture-based flight results
    mock_hotel_search       — fixture-based hotel results
    mock_price_alert        — simulated price fluctuation
    mock_itinerary_store    — in-memory trip records
    mock_booking_handoff_link — constructed mock booking URLs

Future real tools (swapped in Phase 3, same interface):
    Amadeus / Duffel (flights), Booking.com (hotels),
    Google Calendar, Stripe (payments), transport APIs.
"""
