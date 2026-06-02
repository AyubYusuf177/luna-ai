"""
Tests for v0.0.7 — Policy Layer.

Covers:
  - STOP command detection and response.
  - START command detection and response.
  - Passport / national ID keyword blocking.
  - Card number pattern blocking.
  - Payment keyword (CVV, etc.) blocking.
  - Normal messages pass through.
  - Fake booking claim in outbound reply is blocked and rewritten.
  - Normal outbound reply passes.
  - /simulate integration: STOP, START, passport, YES with no pending.
  - /simulate still works for weather, flight, hotel, events.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory
from luna.policy.policy import check_inbound, check_outbound

_NUMBER = "+447700333333"

_PAYLOAD = {"from_number": _NUMBER, "body": "hello"}


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


# ── STOP command ──────────────────────────────────────────────────────────────

def test_stop_returns_stop_command():
    d = check_inbound("STOP")
    assert d.command == "stop"


def test_stop_is_not_allowed():
    d = check_inbound("STOP")
    assert d.allowed is False


def test_stop_has_rewritten_reply():
    d = check_inbound("STOP")
    assert d.rewritten_reply is not None
    assert len(d.rewritten_reply) > 0


def test_stop_case_insensitive():
    assert check_inbound("stop").command == "stop"
    assert check_inbound("Stop").command == "stop"
    assert check_inbound("STOP").command == "stop"


def test_stop_variants():
    for word in ("unsubscribe", "cancel", "quit", "end"):
        d = check_inbound(word)
        assert d.command == "stop", f"Expected stop for '{word}'"


# ── START command ─────────────────────────────────────────────────────────────

def test_start_returns_start_command():
    d = check_inbound("START")
    assert d.command == "start"


def test_start_is_allowed():
    d = check_inbound("START")
    assert d.allowed is True


def test_start_has_rewritten_reply():
    d = check_inbound("START")
    assert d.rewritten_reply is not None
    assert len(d.rewritten_reply) > 0


def test_start_reply_contains_luna():
    d = check_inbound("START")
    assert "Luna" in d.rewritten_reply or "luna" in d.rewritten_reply.lower()


# ── Passport / ID blocking ────────────────────────────────────────────────────

def test_passport_keyword_is_blocked():
    d = check_inbound("my passport number is AB123456")
    assert d.allowed is False


def test_national_id_is_blocked():
    d = check_inbound("national id 12345678")
    assert d.allowed is False


def test_passport_block_has_rewritten_reply():
    d = check_inbound("passport AB123456")
    assert d.rewritten_reply is not None


def test_passport_block_reply_mentions_privacy():
    d = check_inbound("here is my passport number")
    assert "passport" in d.rewritten_reply.lower() or "private" in d.rewritten_reply.lower()


# ── Card number blocking ──────────────────────────────────────────────────────

def test_card_number_is_blocked():
    d = check_inbound("my card is 4111 1111 1111 1111")
    assert d.allowed is False


def test_card_number_no_spaces_is_blocked():
    d = check_inbound("4111111111111111")
    assert d.allowed is False


def test_card_number_block_has_rewritten_reply():
    d = check_inbound("4111 1111 1111 1111")
    assert d.rewritten_reply is not None


# ── Payment keyword blocking ──────────────────────────────────────────────────

def test_cvv_is_blocked():
    d = check_inbound("cvv is 123")
    assert d.allowed is False


def test_iban_is_blocked():
    d = check_inbound("my iban is GB29NWBK")
    assert d.allowed is False


def test_payment_block_has_rewritten_reply():
    d = check_inbound("my cvv is 456")
    assert d.rewritten_reply is not None


# ── Normal messages pass ──────────────────────────────────────────────────────

def test_normal_message_is_allowed():
    d = check_inbound("flights to Tokyo")
    assert d.allowed is True


def test_normal_message_has_no_command():
    d = check_inbound("hotels in Paris")
    assert d.command is None


def test_weather_message_is_allowed():
    d = check_inbound("what's the weather in Rome?")
    assert d.allowed is True


def test_hello_message_is_allowed():
    d = check_inbound("hello")
    assert d.allowed is True


# ── Regression: 'nin' in 'happening' must not trigger passport block ──────────

def test_events_switzerland_not_blocked():
    d = check_inbound("what events are happening in Switzerland next month")
    assert d.allowed is True


def test_events_switzerland_not_passport_blocked():
    d = check_inbound("what events are happening in Switzerland next month")
    assert d.command is None
    assert "passport" not in (d.reason or "").lower()


def test_happening_word_not_blocked():
    d = check_inbound("what is happening in Rome this weekend")
    assert d.allowed is True


def test_planning_word_not_blocked():
    d = check_inbound("I am planning a trip to Berlin")
    assert d.allowed is True


def test_nin_standalone_is_blocked():
    d = check_inbound("my nin is AB123456C")
    assert d.allowed is False


def test_ssn_standalone_is_blocked():
    d = check_inbound("my ssn is 123-45-6789")
    assert d.allowed is False


# ── Outbound policy: fake booking detection ───────────────────────────────────

def test_check_outbound_blocks_i_booked_it():
    d = check_outbound("I booked it for you!")
    assert d.allowed is False


def test_check_outbound_blocks_booking_confirmed():
    d = check_outbound("Your booking is confirmed. Enjoy your trip!")
    assert d.allowed is False


def test_check_outbound_blocks_successfully_booked():
    d = check_outbound("I've successfully booked your flight.")
    assert d.allowed is False


def test_check_outbound_fake_booking_has_rewritten_reply():
    d = check_outbound("I booked your hotel.")
    assert d.rewritten_reply is not None


def test_check_outbound_allows_normal_reply():
    d = check_outbound("Here are some flights from London to Tokyo.")
    assert d.allowed is True


def test_check_outbound_allows_tool_result_reply():
    d = check_outbound("Flights London→Tokyo: BA 08:00 £189 · EZY 13:30 £124. Which would you like?")
    assert d.allowed is True


# ── /simulate integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_stop_returns_opt_out_reply():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={"from_number": _NUMBER, "body": "STOP"})
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert "unsubscribed" in reply.lower() or "opt" in reply.lower() or "start" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_stop_logs_policy_command():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json={"from_number": _NUMBER, "body": "STOP"})
    log_types = [e.event_type for e in events.get_log()]
    assert "policy_command" in log_types


@pytest.mark.asyncio
async def test_simulate_start_returns_opt_in_reply():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={"from_number": _NUMBER, "body": "START"})
    reply = response.json()["reply"]
    assert "luna" in reply.lower() or "welcome" in reply.lower() or "travel" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_passport_message_returns_privacy_reply():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "my passport number is AB123456"},
        )
    reply = response.json()["reply"]
    assert "passport" in reply.lower() or "private" in reply.lower() or "never" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_yes_with_no_pending_returns_safe_reply():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={"from_number": _NUMBER, "body": "YES"})
    reply = response.json()["reply"]
    assert "nothing" in reply.lower() or "confirm" in reply.lower() or "waiting" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_weather_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "weather in Rome"},
        )
    reply = response.json()["reply"]
    assert "Rome" in reply or "weather" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_hotel_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "hotels in Paris"},
        )
    reply = response.json()["reply"]
    assert "Paris" in reply or "hotel" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_flight_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "flights from London to Tokyo"},
        )
    reply = response.json()["reply"]
    assert "London" in reply or "Tokyo" in reply or "flight" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_events_still_works():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "concerts in Madrid"},
        )
    reply = response.json()["reply"]
    assert "Madrid" in reply or "event" in reply.lower() or "concert" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_events_switzerland_not_blocked():
    """Regression: 'happening' contains 'nin'; must not trigger passport block."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "what events are happening in Switzerland next month"},
        )
    reply = response.json()["reply"]
    assert "passport" not in reply.lower()
    assert "private" not in reply.lower()
    assert "Switzerland" in reply or "event" in reply.lower()
