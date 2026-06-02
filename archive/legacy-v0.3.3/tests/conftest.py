"""
tests/conftest.py — Global test fixtures.

Resets ALL in-memory stores before every test so state cannot leak
between test modules. Each store has its own targeted reset so that
mid-test partial resets (e.g. events.reset() in one test) keep working.
"""

import pytest

import luna.config as config_module
from luna.agent import task_manager
from luna.confirmation import store as confirmation_store


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset task and confirmation stores before every test."""
    task_manager.reset_tasks()
    confirmation_store.reset()
    yield


@pytest.fixture(autouse=True)
def _safe_settings():
    """Force test-safe credential settings for every test.

    A local .env with real values (USE_CLAUDE_PLANNER=true, ANTHROPIC_API_KEY,
    TWILIO_ACCOUNT_SID, etc.) would otherwise trigger real external API calls
    during the test suite. This fixture resets credential fields to empty/false
    before each test. Tests that need a credential set should use a monkeypatch
    fixture (e.g. enable_claude) that runs after this one.

    Note: python-dotenv treats inline comments as values when the value before
    the # is empty (e.g. KEY=   # comment → "# comment"), so we also guard
    the Twilio fields against that parsing artefact.
    """
    s = config_module.settings
    saved = {
        "use_claude_planner": s.use_claude_planner,
        "anthropic_api_key": s.anthropic_api_key,
        "twilio_account_sid": s.twilio_account_sid,
        "twilio_auth_token": s.twilio_auth_token,
        "telnyx_api_key": s.telnyx_api_key,
        "weather_provider": s.weather_provider,
    }
    s.use_claude_planner = False
    s.anthropic_api_key = ""
    s.twilio_account_sid = ""
    s.twilio_auth_token = ""
    s.telnyx_api_key = ""
    s.weather_provider = "mock"
    yield
    for attr, val in saved.items():
        setattr(s, attr, val)
