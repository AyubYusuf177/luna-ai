"""
luna/memory/backend.py — Active backend singleton and factory.

The module-level _active backend is set to InMemoryBackend at import
time. This means all sync tests work without touching app startup.

Call init_backend(settings) from the FastAPI lifespan to switch to
SQLite when LUNA_MEMORY_BACKEND=sqlite is configured. The lifespan
replaces _active for the duration of the process.
"""

from luna.memory.backends.in_memory import InMemoryBackend

_active: InMemoryBackend = InMemoryBackend()


def get_backend() -> InMemoryBackend:
    """Return the currently active backend."""
    return _active


def init_backend(settings) -> None:
    """
    Select and initialise the backend from settings.
    Called once at application startup.
    """
    global _active
    if getattr(settings, "luna_memory_backend", "in_memory") == "sqlite":
        from luna.memory.backends.sqlite import SQLiteBackend
        _active = SQLiteBackend(settings.luna_db_path)
    else:
        _active = InMemoryBackend()
