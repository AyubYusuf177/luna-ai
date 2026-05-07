"""
luna/agent/task_manager.py — TravelTask CRUD.

All calls delegate to the active backend (in-memory or SQLite).

Public interface (unchanged from v0.0.4):
    create_task(user_id, source, goal)  → TravelTask
    get_task(task_id)                   → TravelTask | None
    list_active_tasks(user_id)          → list[TravelTask]
    update_task(task)                   → TravelTask
    reset_tasks()                       → None  [tests only]
"""

from datetime import datetime, timezone

from luna.agent.schemas import TravelTask
from luna.memory.backend import get_backend


def create_task(user_id: str, source: str, goal: str) -> TravelTask:
    task = TravelTask(user_id=user_id, source=source, goal=goal)
    return get_backend().create_task(task)


def get_task(task_id: str) -> TravelTask | None:
    return get_backend().get_task(task_id)


def list_active_tasks(user_id: str) -> list[TravelTask]:
    return get_backend().list_active_tasks(user_id)


def update_task(task: TravelTask) -> TravelTask:
    task.updated_at = datetime.now(timezone.utc)
    return get_backend().update_task(task)


def reset_tasks() -> None:
    """Clear all tasks. Does not affect users, conversations, or events."""
    get_backend().reset_tasks()
