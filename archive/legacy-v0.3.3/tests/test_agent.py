"""
Tests for the Agent Runtime Kernel — v0.0.4.

Covers:
  - TravelTask schema creation and field defaults.
  - Task manager CRUD (create, get, list, update, reset).
  - Fallback planner intent classification.
  - Agent Runtime end-to-end via /simulate.
  - Guarantee that no Claude API call occurs in tests.
"""

import pytest
from httpx import ASGITransport, AsyncClient

import luna.config as config_module
from luna.agent import task_manager
from luna.agent.schemas import (
    PlannerOutput,
    RiskLevel,
    TaskPattern,
    TaskStatus,
    TravelTask,
)
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory
from luna.reasoning import planner

_NUMBER = "+447700000000"
_PAYLOAD = {"from_number": _NUMBER, "body": "hello"}


@pytest.fixture(autouse=True)
def reset_state():
    """Reset memory and events before each test (task store reset is in conftest)."""
    memory.reset()
    events.reset()
    yield


# ── TravelTask schema ─────────────────────────────────────────────────────────

def test_travel_task_creates_with_required_fields():
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Flights to Tokyo")
    assert task.user_id == _NUMBER
    assert task.source == "simulate_inbound"
    assert task.goal == "Flights to Tokyo"


def test_travel_task_default_status_is_active():
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    assert task.status == TaskStatus.active


def test_travel_task_default_pattern_is_ask_clarification():
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    assert task.task_pattern == TaskPattern.ask_clarification


def test_travel_task_generates_unique_task_ids():
    t1 = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="A")
    t2 = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="B")
    assert t1.task_id != t2.task_id


def test_travel_task_default_collections_are_empty():
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    assert task.known_fields == {}
    assert task.missing_fields == []
    assert task.candidate_tools == []
    assert task.selected_tools == []


def test_travel_task_has_timestamps():
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    assert task.created_at is not None
    assert task.updated_at is not None


# ── Task manager ──────────────────────────────────────────────────────────────

def test_task_manager_create_returns_travel_task():
    task = task_manager.create_task(_NUMBER, "simulate_inbound", "Find flights")
    assert isinstance(task, TravelTask)
    assert task.user_id == _NUMBER


def test_task_manager_get_returns_created_task():
    task = task_manager.create_task(_NUMBER, "simulate_inbound", "Find hotels")
    fetched = task_manager.get_task(task.task_id)
    assert fetched is not None
    assert fetched.task_id == task.task_id


def test_task_manager_get_returns_none_for_unknown_id():
    result = task_manager.get_task("nonexistent-id")
    assert result is None


def test_task_manager_list_active_tasks_returns_only_active():
    t1 = task_manager.create_task(_NUMBER, "simulate_inbound", "Flights")
    t2 = task_manager.create_task(_NUMBER, "simulate_inbound", "Hotels")
    t2.status = TaskStatus.completed
    task_manager.update_task(t2)

    active = task_manager.list_active_tasks(_NUMBER)
    assert len(active) == 1
    assert active[0].task_id == t1.task_id


def test_task_manager_list_active_tasks_scoped_to_user():
    task_manager.create_task(_NUMBER, "simulate_inbound", "My flight")
    task_manager.create_task("+19999999999", "simulate_inbound", "Other user flight")

    active = task_manager.list_active_tasks(_NUMBER)
    assert len(active) == 1
    assert active[0].user_id == _NUMBER


def test_task_manager_update_persists_changes():
    task = task_manager.create_task(_NUMBER, "simulate_inbound", "Original goal")
    task.goal = "Updated goal"
    task_manager.update_task(task)

    fetched = task_manager.get_task(task.task_id)
    assert fetched.goal == "Updated goal"


def test_task_manager_reset_clears_all_tasks():
    task_manager.create_task(_NUMBER, "simulate_inbound", "Task 1")
    task_manager.create_task(_NUMBER, "simulate_inbound", "Task 2")
    task_manager.reset_tasks()
    assert task_manager.list_active_tasks(_NUMBER) == []


# ── Fallback planner ──────────────────────────────────────────────────────────

def test_fallback_planner_classifies_weather():
    out = planner.run("What's the weather in Rome?", None, [])
    assert out.task_pattern == TaskPattern.answer_with_context
    assert "weather_lookup" in out.candidate_tools


def test_fallback_planner_classifies_flight():
    out = planner.run("Find me flights to Tokyo", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "flight_search" in out.candidate_tools


def test_fallback_planner_classifies_fly():
    out = planner.run("I want to fly from London to NYC", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "flight_search" in out.candidate_tools


def test_fallback_planner_classifies_hotel():
    out = planner.run("Find a hotel in Paris", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "hotel_search" in out.candidate_tools


def test_fallback_planner_classifies_stay():
    out = planner.run("I need somewhere to stay in Barcelona", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "hotel_search" in out.candidate_tools


def test_fallback_planner_classifies_events():
    out = planner.run("Any concerts in Madrid next week?", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "events_search" in out.candidate_tools


def test_fallback_planner_classifies_restaurant():
    out = planner.run("restaurant reservation in Lisbon", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare
    assert "events_search" in out.candidate_tools


def test_fallback_planner_handles_unknown():
    out = planner.run("hello", None, [])
    assert out.task_pattern == TaskPattern.ask_clarification
    assert out.candidate_tools == []


def test_fallback_planner_returns_planner_output_instance():
    out = planner.run("hello", None, [])
    assert isinstance(out, PlannerOutput)


def test_fallback_planner_reply_draft_is_non_empty():
    out = planner.run("hello", None, [])
    assert isinstance(out.reply_draft, str)
    assert len(out.reply_draft) > 0


def test_fallback_planner_weather_reply_draft():
    out = planner.run("weather in Tokyo", None, [])
    assert "weather" in out.reply_draft.lower() or "city" in out.reply_draft.lower()


def test_fallback_planner_flight_reply_draft():
    out = planner.run("flights to Rome", None, [])
    assert "flight" in out.reply_draft.lower()


def test_fallback_planner_hotel_reply_draft():
    out = planner.run("hotels in Berlin", None, [])
    assert "hotel" in out.reply_draft.lower()


def test_fallback_planner_events_reply_draft():
    out = planner.run("events in Vienna", None, [])
    assert "event" in out.reply_draft.lower() or "city" in out.reply_draft.lower()


# ── Agent Runtime via /simulate ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_creates_a_travel_task():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    active = task_manager.list_active_tasks(_NUMBER)
    assert len(active) == 1


@pytest.mark.asyncio
async def test_simulate_task_has_correct_user_id():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    task = task_manager.list_active_tasks(_NUMBER)[0]
    assert task.user_id == _NUMBER


@pytest.mark.asyncio
async def test_simulate_task_has_task_pattern():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json={"from_number": _NUMBER, "body": "find flights to Tokyo"})
    task = task_manager.list_active_tasks(_NUMBER)[0]
    assert task.task_pattern == TaskPattern.search_and_compare


@pytest.mark.asyncio
async def test_simulate_second_message_updates_existing_task():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
        await client.post("/simulate", json={"from_number": _NUMBER, "body": "flights to Rome"})
    # Should still be one task (updated, not duplicated)
    active = task_manager.list_active_tasks(_NUMBER)
    assert len(active) == 1


@pytest.mark.asyncio
async def test_simulate_logs_task_created_event():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
    log_types = [e.event_type for e in events.get_log()]
    assert "task_created" in log_types


@pytest.mark.asyncio
async def test_simulate_logs_task_updated_on_second_message():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/simulate", json=_PAYLOAD)
        events.reset()
        await client.post("/simulate", json={"from_number": _NUMBER, "body": "flights to Tokyo"})
    log_types = [e.event_type for e in events.get_log()]
    assert "task_updated" in log_types


@pytest.mark.asyncio
async def test_simulate_response_comes_from_planner():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate", json={"from_number": _NUMBER, "body": "find me flights to Tokyo"}
        )
    reply = response.json()["reply"]
    # Should contain the flight fallback reply content
    assert "flight" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_unknown_intent_returns_luna_intro():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/simulate", json=_PAYLOAD)
    reply = response.json()["reply"]
    assert "Luna" in reply or "travel" in reply.lower()


# ── Claude planner is disabled in tests ──────────────────────────────────────

def test_claude_planner_is_disabled_by_default():
    """USE_CLAUDE_PLANNER must be false so no Claude calls occur in tests."""
    assert config_module.settings.use_claude_planner is False


def test_anthropic_api_key_is_not_set_in_tests():
    """ANTHROPIC_API_KEY must be empty so even if planner flag were set, no call occurs."""
    assert config_module.settings.anthropic_api_key == ""


def test_planner_uses_fallback_when_claude_disabled(monkeypatch):
    """Explicitly confirm fallback is used when use_claude_planner=False."""
    monkeypatch.setattr(config_module.settings, "use_claude_planner", False)
    out = planner.run("flights to Paris", None, [])
    assert out.task_pattern == TaskPattern.search_and_compare  # fallback result
