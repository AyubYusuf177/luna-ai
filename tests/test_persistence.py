"""
Tests for v0.0.6 — SQLite persistence backend.

All SQLite tests use a tmp_path-scoped database so they never touch
the real ./data/luna.db and never affect the global in-memory backend
used by the rest of the test suite.

Covers:
  - SQLite backend creates the database file.
  - SQLite backend creates the four tables.
  - User persists across backend re-instantiation (simulates server restart).
  - Conversation turn persists across re-instantiation.
  - TravelTask persists across re-instantiation.
  - Event log entry persists across re-instantiation.
  - JSON fields (known_fields, missing_fields, candidate_tools) round-trip.
  - InMemoryBackend still works as a standalone class.
  - /simulate still works with the default in-memory backend.
  - All previous tests still pass (implicitly — no regressions).
"""

import sqlite3

import pytest
from httpx import ASGITransport, AsyncClient

from luna.agent.schemas import RiskLevel, TaskPattern, TaskStatus, TravelTask
from luna.events.schemas import EventLogEntry
from luna.main import app
from luna.memory.backends.in_memory import InMemoryBackend
from luna.memory.backends.sqlite import SQLiteBackend
from luna.memory.schemas import ConversationTurn, UserProfile

_NUMBER = "+447700222222"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path) -> str:
    return str(tmp_path / "test_luna.db")


@pytest.fixture()
def sqlite_backend(db_path) -> SQLiteBackend:
    return SQLiteBackend(db_path)


# ── SQLite: file and table creation ──────────────────────────────────────────

def test_sqlite_creates_database_file(db_path):
    SQLiteBackend(db_path)
    import os
    assert os.path.exists(db_path)


def test_sqlite_creates_users_table(db_path):
    SQLiteBackend(db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "users" in tables


def test_sqlite_creates_conversation_turns_table(db_path):
    SQLiteBackend(db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "conversation_turns" in tables


def test_sqlite_creates_tasks_table(db_path):
    SQLiteBackend(db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "tasks" in tables


def test_sqlite_creates_event_log_table(db_path):
    SQLiteBackend(db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "event_log" in tables


# ── SQLite: user persistence across restarts ──────────────────────────────────

def test_sqlite_user_persists_across_restart(db_path):
    b1 = SQLiteBackend(db_path)
    b1.create_user(_NUMBER)

    b2 = SQLiteBackend(db_path)  # simulates server restart
    user = b2.get_user(_NUMBER)
    assert user is not None
    assert user.user_id == _NUMBER


def test_sqlite_user_is_none_before_creation(sqlite_backend):
    assert sqlite_backend.get_user(_NUMBER) is None


def test_sqlite_create_user_returns_profile(sqlite_backend):
    profile = sqlite_backend.create_user(_NUMBER)
    assert isinstance(profile, UserProfile)
    assert profile.user_id == _NUMBER


def test_sqlite_user_created_at_is_preserved(db_path):
    b1 = SQLiteBackend(db_path)
    created = b1.create_user(_NUMBER)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_user(_NUMBER)
    assert restored.created_at.replace(microsecond=0) == created.created_at.replace(microsecond=0)


# ── SQLite: conversation persistence across restarts ──────────────────────────

def test_sqlite_conversation_persists_across_restart(db_path):
    b1 = SQLiteBackend(db_path)
    b1.append_turn(_NUMBER, "user", "hello")

    b2 = SQLiteBackend(db_path)
    turns = b2.get_conversation(_NUMBER)
    assert len(turns) == 1
    assert turns[0].role == "user"
    assert turns[0].body == "hello"


def test_sqlite_conversation_turn_returns_correct_type(sqlite_backend):
    turn = sqlite_backend.append_turn(_NUMBER, "luna", "Hi there")
    assert isinstance(turn, ConversationTurn)


def test_sqlite_multiple_turns_preserved_in_order(db_path):
    b1 = SQLiteBackend(db_path)
    b1.append_turn(_NUMBER, "user", "first")
    b1.append_turn(_NUMBER, "luna", "second")
    b1.append_turn(_NUMBER, "user", "third")

    b2 = SQLiteBackend(db_path)
    turns = b2.get_conversation(_NUMBER)
    assert len(turns) == 3
    assert [t.body for t in turns] == ["first", "second", "third"]


# ── SQLite: task persistence across restarts ──────────────────────────────────

def test_sqlite_task_persists_across_restart(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Flights to Tokyo")
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored is not None
    assert restored.task_id == task.task_id
    assert restored.goal == "Flights to Tokyo"


def test_sqlite_task_get_returns_none_for_unknown(sqlite_backend):
    assert sqlite_backend.get_task("no-such-id") is None


def test_sqlite_list_active_tasks_after_restart(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Hotels in Paris")
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    active = b2.list_active_tasks(_NUMBER)
    assert len(active) == 1
    assert active[0].goal == "Hotels in Paris"


def test_sqlite_task_update_persists(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Original")
    b1.create_task(task)
    task.goal = "Updated"
    b1.update_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored.goal == "Updated"


def test_sqlite_completed_task_not_in_active_list(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    b1.create_task(task)
    task.status = TaskStatus.completed
    b1.update_task(task)

    b2 = SQLiteBackend(db_path)
    assert b2.list_active_tasks(_NUMBER) == []


# ── SQLite: JSON field round-trip ─────────────────────────────────────────────

def test_sqlite_task_known_fields_round_trip(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(
        user_id=_NUMBER,
        source="simulate_inbound",
        goal="Flights",
        known_fields={"origin": "London", "destination": "Tokyo"},
    )
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored.known_fields == {"origin": "London", "destination": "Tokyo"}


def test_sqlite_task_missing_fields_round_trip(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(
        user_id=_NUMBER,
        source="simulate_inbound",
        goal="Flights",
        missing_fields=["depart_date", "return_date", "passengers"],
    )
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored.missing_fields == ["depart_date", "return_date", "passengers"]


def test_sqlite_task_candidate_tools_round_trip(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(
        user_id=_NUMBER,
        source="simulate_inbound",
        goal="Search",
        candidate_tools=["flight_search", "hotel_search"],
    )
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored.candidate_tools == ["flight_search", "hotel_search"]


def test_sqlite_task_enums_round_trip(db_path):
    b1 = SQLiteBackend(db_path)
    task = TravelTask(
        user_id=_NUMBER,
        source="simulate_inbound",
        goal="Test",
        task_pattern=TaskPattern.search_and_compare,
        risk_level=RiskLevel.medium,
        status=TaskStatus.pending_confirmation,
    )
    b1.create_task(task)

    b2 = SQLiteBackend(db_path)
    restored = b2.get_task(task.task_id)
    assert restored.task_pattern == TaskPattern.search_and_compare
    assert restored.risk_level == RiskLevel.medium
    assert restored.status == TaskStatus.pending_confirmation


# ── SQLite: event log persistence across restarts ─────────────────────────────

def test_sqlite_event_log_persists_across_restart(db_path):
    b1 = SQLiteBackend(db_path)
    b1.log_event("inbound_sms_received", _NUMBER, {"body": "hello"})

    b2 = SQLiteBackend(db_path)
    log = b2.get_event_log()
    assert len(log) == 1
    assert log[0].event_type == "inbound_sms_received"


def test_sqlite_event_log_entry_is_correct_type(sqlite_backend):
    entry = sqlite_backend.log_event("test_event", _NUMBER, {})
    assert isinstance(entry, EventLogEntry)


def test_sqlite_event_metadata_round_trip(db_path):
    b1 = SQLiteBackend(db_path)
    b1.log_event("tool_executed", _NUMBER, {"tool_name": "weather_lookup", "status": "ok"})

    b2 = SQLiteBackend(db_path)
    entry = b2.get_event_log()[0]
    assert entry.metadata["tool_name"] == "weather_lookup"
    assert entry.metadata["status"] == "ok"


def test_sqlite_multiple_events_preserved(db_path):
    b1 = SQLiteBackend(db_path)
    b1.log_event("event_a", _NUMBER, {})
    b1.log_event("event_b", _NUMBER, {})

    b2 = SQLiteBackend(db_path)
    types = [e.event_type for e in b2.get_event_log()]
    assert "event_a" in types
    assert "event_b" in types


# ── SQLite: resets ────────────────────────────────────────────────────────────

def test_sqlite_reset_users_clears_only_users(sqlite_backend):
    sqlite_backend.create_user(_NUMBER)
    sqlite_backend.append_turn(_NUMBER, "user", "hi")
    sqlite_backend.reset_users()
    assert sqlite_backend.get_user(_NUMBER) is None
    assert len(sqlite_backend.get_conversation(_NUMBER)) == 1


def test_sqlite_reset_events_clears_only_events(sqlite_backend):
    sqlite_backend.create_user(_NUMBER)
    sqlite_backend.log_event("e", _NUMBER, {})
    sqlite_backend.reset_events()
    assert sqlite_backend.get_event_log() == []
    assert sqlite_backend.get_user(_NUMBER) is not None


# ── InMemoryBackend still works standalone ────────────────────────────────────

def test_in_memory_backend_user_round_trip():
    b = InMemoryBackend()
    b.create_user(_NUMBER)
    assert b.get_user(_NUMBER) is not None


def test_in_memory_backend_conversation_round_trip():
    b = InMemoryBackend()
    b.append_turn(_NUMBER, "user", "hello")
    turns = b.get_conversation(_NUMBER)
    assert len(turns) == 1
    assert turns[0].body == "hello"


def test_in_memory_backend_task_round_trip():
    b = InMemoryBackend()
    task = TravelTask(user_id=_NUMBER, source="simulate_inbound", goal="Test")
    b.create_task(task)
    assert b.get_task(task.task_id) is not None


def test_in_memory_backend_event_round_trip():
    b = InMemoryBackend()
    b.log_event("test", _NUMBER, {})
    assert len(b.get_event_log()) == 1


def test_in_memory_backend_resets_are_granular():
    b = InMemoryBackend()
    b.create_user(_NUMBER)
    b.log_event("e", _NUMBER, {})
    b.reset_events()
    assert b.get_user(_NUMBER) is not None   # user still there
    assert b.get_event_log() == []           # events gone


# ── /simulate still works with default in-memory backend ─────────────────────

@pytest.mark.asyncio
async def test_simulate_works_with_in_memory_backend():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "hotels in Rome"},
        )
    assert response.status_code == 200
    assert "reply" in response.json()


@pytest.mark.asyncio
async def test_simulate_reply_is_non_empty_with_in_memory_backend():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "flights from London to Paris"},
        )
    reply = response.json()["reply"]
    assert len(reply) > 0
