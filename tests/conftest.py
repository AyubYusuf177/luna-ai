"""
tests/conftest.py — Global test fixtures.

Resets ALL in-memory stores before every test so state cannot leak
between test modules. Each store has its own targeted reset so that
mid-test partial resets (e.g. events.reset() in one test) keep working.
"""

import pytest

from luna.agent import task_manager
from luna.confirmation import store as confirmation_store


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset task and confirmation stores before every test."""
    task_manager.reset_tasks()
    confirmation_store.reset()
    yield
