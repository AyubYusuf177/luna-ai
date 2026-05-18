"""
Tests for v0.0.5 — Tool Registry, Dispatcher, Mock Tools, and Runtime integration.

Covers:
  - ToolDefinition schema.
  - Registry: register, get, all_tools.
  - Dispatcher: ok path, missing_args, unknown tool, disabled tool.
  - Mock tools: weather_lookup, flight_search, hotel_search, events_search.
  - Fallback planner: known_fields extraction from natural language.
  - Agent Runtime: tool_executed event, reply from ToolResult.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from luna.agent import task_manager
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory
from luna.reasoning import planner
from luna.tools import dispatcher, registry
from luna.tools.schemas import ToolDefinition, ToolRequest, ToolResult, ToolStatus
from luna.agent.schemas import RiskLevel, TaskPattern

_NUMBER = "+447700111111"


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


# ── ToolDefinition schema ─────────────────────────────────────────────────────

def test_tool_definition_fields():
    td = ToolDefinition(
        name="test_tool",
        description="A test tool.",
        risk_level=RiskLevel.low,
    )
    assert td.name == "test_tool"
    assert td.is_mock is True
    assert td.enabled_in_v0 is True


def test_tool_request_defaults():
    req = ToolRequest(tool_name="weather_lookup")
    assert req.args == {}


def test_tool_result_fields():
    result = ToolResult(
        tool_name="weather_lookup",
        status=ToolStatus.ok,
        data={"city": "Rome"},
        reply_text="Rome: Sunny.",
    )
    assert result.status == ToolStatus.ok
    assert result.data["city"] == "Rome"


# ── Tool Registry ─────────────────────────────────────────────────────────────

def test_registry_has_weather_lookup():
    assert registry.get("weather_lookup") is not None


def test_registry_has_flight_search():
    assert registry.get("flight_search") is not None


def test_registry_has_hotel_search():
    assert registry.get("hotel_search") is not None


def test_registry_has_events_search():
    assert registry.get("events_search") is not None


def test_registry_returns_none_for_unknown():
    assert registry.get("nonexistent_tool") is None


def test_registry_all_tools_returns_four():
    tools = registry.all_tools()
    names = {t.name for t in tools}
    assert {"weather_lookup", "flight_search", "hotel_search", "events_search"}.issubset(names)


def test_registry_tool_is_low_risk():
    td = registry.get("weather_lookup")
    assert td.risk_level == RiskLevel.low


def test_registry_tool_is_mock():
    td = registry.get("flight_search")
    assert td.is_mock is True


def test_registry_tool_is_enabled():
    td = registry.get("hotel_search")
    assert td.enabled_in_v0 is True


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def test_dispatcher_weather_lookup_ok():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup",
        args={"city": "Rome"},
    ))
    assert result.status == ToolStatus.ok
    assert "Rome" in result.reply_text


async def test_dispatcher_weather_lookup_missing_args():
    result = await dispatcher.dispatch(ToolRequest(tool_name="weather_lookup"))
    assert result.status == ToolStatus.missing_args


async def test_dispatcher_flight_search_ok():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="flight_search",
        args={"origin": "London", "destination": "Tokyo"},
    ))
    assert result.status == ToolStatus.ok
    assert "London" in result.reply_text
    assert "Tokyo" in result.reply_text


async def test_dispatcher_flight_search_missing_args():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="flight_search",
        args={"origin": "London"},
    ))
    assert result.status == ToolStatus.missing_args


async def test_dispatcher_hotel_search_ok():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="hotel_search",
        args={"city": "Paris"},
    ))
    assert result.status == ToolStatus.ok
    assert "Paris" in result.reply_text


async def test_dispatcher_hotel_search_missing_args():
    result = await dispatcher.dispatch(ToolRequest(tool_name="hotel_search"))
    assert result.status == ToolStatus.missing_args


async def test_dispatcher_events_search_ok():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="events_search",
        args={"city": "Madrid"},
    ))
    assert result.status == ToolStatus.ok
    assert "Madrid" in result.reply_text


async def test_dispatcher_events_search_missing_args():
    result = await dispatcher.dispatch(ToolRequest(tool_name="events_search"))
    assert result.status == ToolStatus.missing_args


async def test_dispatcher_unknown_tool_returns_error():
    result = await dispatcher.dispatch(ToolRequest(tool_name="does_not_exist"))
    assert result.status == ToolStatus.error


async def test_dispatcher_returns_tool_result_instance():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup",
        args={"city": "Berlin"},
    ))
    assert isinstance(result, ToolResult)


async def test_dispatcher_ok_result_has_data():
    result = await dispatcher.dispatch(ToolRequest(
        tool_name="weather_lookup",
        args={"city": "Berlin"},
    ))
    assert "city" in result.data


# ── Fallback planner: known_fields extraction ─────────────────────────────────

def test_planner_extracts_city_from_in_clause():
    out = planner.run("hotels in Paris", None, [])
    assert out.known_fields.get("city") == "Paris"


def test_planner_extracts_destination_from_to_clause():
    out = planner.run("flights to Tokyo", None, [])
    assert out.known_fields.get("destination") == "Tokyo"


def test_planner_extracts_origin_and_destination_from_from_to():
    out = planner.run("flights from London to Paris", None, [])
    assert out.known_fields.get("origin") == "London"
    assert out.known_fields.get("destination") == "Paris"


def test_planner_selects_tool_when_city_known_for_weather():
    out = planner.run("weather in Rome", None, [])
    assert "weather_lookup" in out.selected_tools


def test_planner_no_selected_tool_when_city_missing_for_weather():
    out = planner.run("what's the weather like?", None, [])
    assert out.selected_tools == []


def test_planner_selects_tool_when_hotel_city_known():
    out = planner.run("hotels in Berlin", None, [])
    assert "hotel_search" in out.selected_tools


def test_planner_selects_tool_when_events_city_known():
    out = planner.run("concerts in Vienna", None, [])
    assert "events_search" in out.selected_tools


def test_planner_selects_flight_tool_when_route_known():
    out = planner.run("fly from London to New York", None, [])
    assert "flight_search" in out.selected_tools


def test_planner_no_flight_tool_when_route_incomplete():
    out = planner.run("find me flights", None, [])
    assert out.selected_tools == []


# ── Agent Runtime integration ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_runtime_logs_tool_executed_when_tool_selected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "weather in Rome",
        })
    log_types = [e.event_type for e in events.get_log()]
    assert "tool_executed" in log_types


@pytest.mark.asyncio
async def test_runtime_reply_comes_from_tool_when_city_known():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "weather in Rome",
        })
    reply = response.json()["reply"]
    assert "Rome" in reply


@pytest.mark.asyncio
async def test_runtime_reply_from_planner_when_no_tool_selected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "what's the weather like?",
        })
    reply = response.json()["reply"]
    # No city → falls back to planner draft asking for city
    assert len(reply) > 0


@pytest.mark.asyncio
async def test_runtime_hotel_search_reply_contains_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "find hotels in Berlin",
        })
    reply = response.json()["reply"]
    assert "Berlin" in reply


@pytest.mark.asyncio
async def test_runtime_flight_search_reply_contains_route():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "flights from London to Tokyo",
        })
    reply = response.json()["reply"]
    assert "London" in reply
    assert "Tokyo" in reply


@pytest.mark.asyncio
async def test_runtime_no_tool_executed_for_unknown_intent():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "hello",
        })
    log_types = [e.event_type for e in events.get_log()]
    assert "tool_executed" not in log_types


@pytest.mark.asyncio
async def test_runtime_task_has_known_fields_after_tool_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json={
            "from_number": _NUMBER,
            "body": "hotels in Paris",
        })
    tasks = task_manager.list_active_tasks(_NUMBER)
    assert tasks[0].known_fields.get("city") == "Paris"
