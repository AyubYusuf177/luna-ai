"""
luna/memory/backends/sqlite.py — SQLite persistence backend.

Pure stdlib (sqlite3). No extra dependencies.
Used when LUNA_MEMORY_BACKEND=sqlite.

Creates the database file and all tables on first instantiation.
JSON columns store dicts and lists that can't map to scalar SQL types.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from luna.agent.schemas import RiskLevel, TaskPattern, TaskStatus, TravelTask
from luna.events.schemas import EventLogEntry
from luna.memory.schemas import ConversationTurn, UserProfile

_SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id    TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
)
"""

_SQL_CREATE_TURNS = """
CREATE TABLE IF NOT EXISTS conversation_turns (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    role       TEXT NOT NULL,
    body       TEXT NOT NULL,
    timestamp  TEXT NOT NULL
)
"""

_SQL_CREATE_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id         TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    source          TEXT NOT NULL,
    goal            TEXT NOT NULL,
    task_pattern    TEXT NOT NULL,
    status          TEXT NOT NULL,
    known_fields    TEXT NOT NULL,
    missing_fields  TEXT NOT NULL,
    candidate_tools TEXT NOT NULL,
    selected_tools  TEXT NOT NULL,
    risk_level      TEXT NOT NULL,
    next_action     TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
)
"""

_SQL_CREATE_EVENTS = """
CREATE TABLE IF NOT EXISTS event_log (
    event_id   TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    event_type TEXT NOT NULL,
    metadata   TEXT NOT NULL,
    timestamp  TEXT NOT NULL
)
"""


class SQLiteBackend:
    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._init_tables()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(_SQL_CREATE_USERS)
            conn.execute(_SQL_CREATE_TURNS)
            conn.execute(_SQL_CREATE_TASKS)
            conn.execute(_SQL_CREATE_EVENTS)

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_user(self, user_id: str) -> UserProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, created_at FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        return UserProfile(
            user_id=row["user_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def create_user(self, user_id: str) -> UserProfile:
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
                (user_id, now.isoformat()),
            )
        return UserProfile(user_id=user_id, created_at=now)

    # ── Conversations ─────────────────────────────────────────────────────────

    def get_conversation(self, user_id: str) -> list[ConversationTurn]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, body, timestamp FROM conversation_turns"
                " WHERE user_id = ? ORDER BY id",
                (user_id,),
            ).fetchall()
        return [
            ConversationTurn(
                role=r["role"],
                body=r["body"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
            for r in rows
        ]

    def append_turn(self, user_id: str, role: str, body: str) -> ConversationTurn:
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversation_turns (user_id, role, body, timestamp)"
                " VALUES (?, ?, ?, ?)",
                (user_id, role, body, now.isoformat()),
            )
        return ConversationTurn(role=role, body=body, timestamp=now)

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def create_task(self, task: TravelTask) -> TravelTask:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO tasks
                   (task_id, user_id, source, goal, task_pattern, status,
                    known_fields, missing_fields, candidate_tools, selected_tools,
                    risk_level, next_action, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.task_id,
                    task.user_id,
                    task.source,
                    task.goal,
                    task.task_pattern.value,
                    task.status.value,
                    json.dumps(task.known_fields),
                    json.dumps(task.missing_fields),
                    json.dumps(task.candidate_tools),
                    json.dumps(task.selected_tools),
                    task.risk_level.value,
                    task.next_action,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                ),
            )
        return task

    def get_task(self, task_id: str) -> TravelTask | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
        return self._row_to_task(row) if row else None

    def list_active_tasks(self, user_id: str) -> list[TravelTask]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? AND status = 'active'"
                " ORDER BY created_at",
                (user_id,),
            ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update_task(self, task: TravelTask) -> TravelTask:
        with self._connect() as conn:
            conn.execute(
                """UPDATE tasks SET
                   goal = ?, task_pattern = ?, status = ?,
                   known_fields = ?, missing_fields = ?,
                   candidate_tools = ?, selected_tools = ?,
                   risk_level = ?, next_action = ?, updated_at = ?
                   WHERE task_id = ?""",
                (
                    task.goal,
                    task.task_pattern.value,
                    task.status.value,
                    json.dumps(task.known_fields),
                    json.dumps(task.missing_fields),
                    json.dumps(task.candidate_tools),
                    json.dumps(task.selected_tools),
                    task.risk_level.value,
                    task.next_action,
                    task.updated_at.isoformat(),
                    task.task_id,
                ),
            )
        return task

    def _row_to_task(self, row: sqlite3.Row) -> TravelTask:
        return TravelTask(
            task_id=row["task_id"],
            user_id=row["user_id"],
            source=row["source"],
            goal=row["goal"],
            task_pattern=TaskPattern(row["task_pattern"]),
            status=TaskStatus(row["status"]),
            known_fields=json.loads(row["known_fields"]),
            missing_fields=json.loads(row["missing_fields"]),
            candidate_tools=json.loads(row["candidate_tools"]),
            selected_tools=json.loads(row["selected_tools"]),
            risk_level=RiskLevel(row["risk_level"]),
            next_action=row["next_action"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ── Events ────────────────────────────────────────────────────────────────

    def log_event(self, event_type: str, user_id: str, metadata: dict) -> EventLogEntry:
        event_id = str(uuid4())
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO event_log (event_id, user_id, event_type, metadata, timestamp)"
                " VALUES (?, ?, ?, ?, ?)",
                (event_id, user_id, event_type, json.dumps(metadata), now.isoformat()),
            )
        return EventLogEntry(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            timestamp=now,
            metadata=metadata,
        )

    def get_event_log(self) -> list[EventLogEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM event_log ORDER BY timestamp"
            ).fetchall()
        return [
            EventLogEntry(
                event_id=r["event_id"],
                user_id=r["user_id"],
                event_type=r["event_type"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

    # ── Resets ────────────────────────────────────────────────────────────────

    def reset_users(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM users")

    def reset_conversations(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM conversation_turns")

    def reset_tasks(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks")

    def reset_events(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM event_log")
