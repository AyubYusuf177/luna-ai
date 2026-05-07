"""
luna/agent/task_manager.py — In-memory TravelTask store.

Simple CRUD for TravelTask objects keyed by task_id.
All state is module-level (lost on restart) — acceptable for v0.1.
SQLite persistence is introduced in v0.0.6 behind the same interface.

Public interface:
    create_task(user_id, source, goal)  → TravelTask
    get_task(task_id)                   → TravelTask | None
    list_active_tasks(user_id)          → list[TravelTask]
    update_task(task)                   → TravelTask
    reset_tasks()                       → None  [tests only]
"""

from datetime import datetime, timezone

from luna.agent.schemas import TaskStatus, TravelTask

# ── Store ─────────────────────────────────────────────────────────────────────

_tasks: dict[str, TravelTask] = {}


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_task(user_id: str, source: str, goal: str) -> TravelTask:
    """
    Create a new TravelTask with default values and persist it.

    The planner will populate task_pattern, known_fields, candidate_tools,
    etc. immediately after creation. Status defaults to active.
    """
    task = TravelTask(user_id=user_id, source=source, goal=goal)
    _tasks[task.task_id] = task
    return task


def get_task(task_id: str) -> TravelTask | None:
    """Return the task with task_id, or None if not found."""
    return _tasks.get(task_id)


def list_active_tasks(user_id: str) -> list[TravelTask]:
    """Return all tasks for user_id with status=active, ordered by created_at."""
    return sorted(
        [t for t in _tasks.values() if t.user_id == user_id and t.status == TaskStatus.active],
        key=lambda t: t.created_at,
    )


def update_task(task: TravelTask) -> TravelTask:
    """Persist an updated TravelTask. Overwrites the existing record."""
    task.updated_at = datetime.now(timezone.utc)
    _tasks[task.task_id] = task
    return task


# ── Test utility ──────────────────────────────────────────────────────────────

def reset_tasks() -> None:
    """Clear all task state. Call from test fixtures only."""
    _tasks.clear()
