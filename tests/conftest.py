"""
tests/conftest.py — Global test fixtures.

Provides a single autouse fixture that resets ALL in-memory stores before
every test. This prevents state from leaking between test modules.

Each test file also has its own reset fixture for memory and events
(from v0.0.2). This conftest adds task_manager reset so the new agent
tests are always isolated without modifying existing test files.

If a test file already resets memory/events, that reset runs in addition
to this one — both are idempotent so there is no conflict.
"""

import pytest

from luna.agent import task_manager


@pytest.fixture(autouse=True)
def reset_task_store():
    """Reset the in-memory task store before every test."""
    task_manager.reset_tasks()
    yield
