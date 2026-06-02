"""
luna/memory/backends/in_memory.py — In-memory backend (default, tests).

State is lost on process exit. Used in all tests and as the startup
default when LUNA_MEMORY_BACKEND is not set to "sqlite".
"""

from datetime import datetime, timezone
from uuid import uuid4

from luna.agent.schemas import TaskStatus, TravelTask
from luna.events.schemas import EventLogEntry
from luna.memory.schemas import ConversationTurn, UserProfile


class InMemoryBackend:
    def __init__(self) -> None:
        self._users: dict[str, UserProfile] = {}
        self._conversations: dict[str, list[ConversationTurn]] = {}
        self._tasks: dict[str, TravelTask] = {}
        self._log: list[EventLogEntry] = []

    # ── Users ─────────────────────────────────────────────────────────────────

    def get_user(self, user_id: str) -> UserProfile | None:
        return self._users.get(user_id)

    def create_user(self, user_id: str) -> UserProfile:
        profile = UserProfile(user_id=user_id, created_at=datetime.now(timezone.utc))
        self._users[user_id] = profile
        return profile

    # ── Conversations ─────────────────────────────────────────────────────────

    def get_conversation(self, user_id: str) -> list[ConversationTurn]:
        return self._conversations.get(user_id, [])

    def append_turn(self, user_id: str, role: str, body: str) -> ConversationTurn:
        turn = ConversationTurn(role=role, body=body, timestamp=datetime.now(timezone.utc))
        self._conversations.setdefault(user_id, []).append(turn)
        return turn

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def create_task(self, task: TravelTask) -> TravelTask:
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> TravelTask | None:
        return self._tasks.get(task_id)

    def list_active_tasks(self, user_id: str) -> list[TravelTask]:
        return sorted(
            [t for t in self._tasks.values()
             if t.user_id == user_id and t.status == TaskStatus.active],
            key=lambda t: t.created_at,
        )

    def update_task(self, task: TravelTask) -> TravelTask:
        self._tasks[task.task_id] = task
        return task

    # ── Events ────────────────────────────────────────────────────────────────

    def log_event(self, event_type: str, user_id: str, metadata: dict) -> EventLogEntry:
        entry = EventLogEntry(
            event_id=str(uuid4()),
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata,
        )
        self._log.append(entry)
        return entry

    def get_event_log(self) -> list[EventLogEntry]:
        return list(self._log)

    # ── Resets (test isolation — granular so mid-test resets stay correct) ────

    def reset_users(self) -> None:
        self._users.clear()

    def reset_conversations(self) -> None:
        self._conversations.clear()

    def reset_tasks(self) -> None:
        self._tasks.clear()

    def reset_events(self) -> None:
        self._log.clear()
