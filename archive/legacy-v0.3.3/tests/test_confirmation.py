"""
Tests for v0.0.7 — Confirmation System (store + resolver).

Covers:
  - store.create returns PendingConfirmation with pending status.
  - store.get_pending returns it, None before create.
  - Second create for same user replaces first (one pending per user).
  - store.resolve updates status and clears pending index.
  - resolver: YES confirms pending confirmation.
  - resolver: NO rejects pending confirmation.
  - resolver: YES with no pending returns handled=True with safe reply.
  - resolver: NO with no pending returns None (not handled).
  - resolver: expired confirmation returns handled=True with expired reply.
  - resolver: normal message (non YES/NO) returns None.
  - resolver: confirmed status is correct after YES.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from luna.confirmation import store
from luna.confirmation.resolver import resolve_inbound
from luna.confirmation.schemas import ConfirmationStatus, PendingConfirmation
from luna.events import logger as events
from luna.main import app
from luna.memory import store as memory

_NUMBER = "+447700444444"
_TASK_ID = "task-test-001"


@pytest.fixture(autouse=True)
def reset_state():
    memory.reset()
    events.reset()
    yield


def _make_confirmation(**kwargs) -> PendingConfirmation:
    defaults = dict(
        user_id=_NUMBER,
        task_id=_TASK_ID,
        action_type="test_action",
        human_summary="Book a test flight",
    )
    defaults.update(kwargs)
    return store.create(**defaults)


# ── store.create ──────────────────────────────────────────────────────────────

def test_create_returns_pending_confirmation():
    c = _make_confirmation()
    assert isinstance(c, PendingConfirmation)


def test_create_sets_pending_status():
    c = _make_confirmation()
    assert c.status == ConfirmationStatus.pending


def test_create_sets_correct_user_id():
    c = _make_confirmation()
    assert c.user_id == _NUMBER


def test_create_sets_human_summary():
    c = _make_confirmation(human_summary="Search for hotels in Paris")
    assert c.human_summary == "Search for hotels in Paris"


def test_create_sets_expires_at_in_future():
    c = _make_confirmation()
    assert c.expires_at > c.created_at


def test_create_generates_unique_confirmation_ids():
    c1 = store.create(_NUMBER, _TASK_ID, "a", "First")
    c2 = store.create(_NUMBER + "1", _TASK_ID, "a", "Second")
    assert c1.confirmation_id != c2.confirmation_id


# ── store.get_pending ─────────────────────────────────────────────────────────

def test_get_pending_returns_confirmation_after_create():
    c = _make_confirmation()
    pending = store.get_pending(_NUMBER)
    assert pending is not None
    assert pending.confirmation_id == c.confirmation_id


def test_get_pending_returns_none_before_create():
    assert store.get_pending(_NUMBER) is None


def test_get_pending_returns_none_for_unknown_user():
    _make_confirmation()
    assert store.get_pending("+10000000000") is None


# ── One pending per user ──────────────────────────────────────────────────────

def test_second_create_replaces_first():
    store.create(_NUMBER, _TASK_ID, "first", "First action")
    c2 = store.create(_NUMBER, _TASK_ID, "second", "Second action")
    pending = store.get_pending(_NUMBER)
    assert pending.confirmation_id == c2.confirmation_id
    assert pending.human_summary == "Second action"


def test_second_create_only_one_pending_remains():
    store.create(_NUMBER, _TASK_ID, "first", "First")
    store.create(_NUMBER, _TASK_ID, "second", "Second")
    # get_pending should return the second, not the first
    pending = store.get_pending(_NUMBER)
    assert pending.action_type == "second"


# ── store.resolve ─────────────────────────────────────────────────────────────

def test_resolve_updates_status_to_confirmed():
    c = _make_confirmation()
    resolved = store.resolve(c.confirmation_id, ConfirmationStatus.confirmed)
    assert resolved.status == ConfirmationStatus.confirmed


def test_resolve_updates_status_to_rejected():
    c = _make_confirmation()
    resolved = store.resolve(c.confirmation_id, ConfirmationStatus.rejected)
    assert resolved.status == ConfirmationStatus.rejected


def test_resolve_clears_pending_for_user():
    c = _make_confirmation()
    store.resolve(c.confirmation_id, ConfirmationStatus.confirmed)
    assert store.get_pending(_NUMBER) is None


def test_resolve_returns_none_for_unknown_id():
    result = store.resolve("nonexistent-id", ConfirmationStatus.confirmed)
    assert result is None


# ── resolver: YES confirms ────────────────────────────────────────────────────

def test_yes_confirms_pending_confirmation():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "YES")
    assert result is not None
    assert result.handled is True
    assert result.confirmation.status == ConfirmationStatus.confirmed


def test_yes_clears_pending_after_confirm():
    _make_confirmation()
    resolve_inbound(_NUMBER, "YES")
    assert store.get_pending(_NUMBER) is None


def test_yes_reply_contains_confirmation_summary():
    _make_confirmation(human_summary="Book test flight")
    result = resolve_inbound(_NUMBER, "YES")
    assert "Book test flight" in result.reply or "confirmed" in result.reply.lower()


def test_yes_case_insensitive():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "yes")
    assert result is not None and result.handled is True


def test_yes_ok_synonym_confirms():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "ok")
    assert result is not None and result.handled is True


# ── resolver: NO rejects ──────────────────────────────────────────────────────

def test_no_rejects_pending_confirmation():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "NO")
    assert result is not None
    assert result.handled is True
    assert result.confirmation.status == ConfirmationStatus.rejected


def test_no_clears_pending_after_reject():
    _make_confirmation()
    resolve_inbound(_NUMBER, "NO")
    assert store.get_pending(_NUMBER) is None


def test_no_reply_mentions_cancelled():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "NO")
    assert "cancel" in result.reply.lower() or "no" in result.reply.lower()


# ── resolver: YES with no pending ─────────────────────────────────────────────

def test_yes_with_no_pending_is_handled():
    result = resolve_inbound(_NUMBER, "YES")
    assert result is not None
    assert result.handled is True


def test_yes_with_no_pending_reply_is_safe():
    result = resolve_inbound(_NUMBER, "YES")
    assert "nothing" in result.reply.lower() or "waiting" in result.reply.lower() or "confirm" in result.reply.lower()


def test_yes_with_no_pending_has_no_confirmation_object():
    result = resolve_inbound(_NUMBER, "YES")
    assert result.confirmation is None


# ── resolver: NO with no pending ─────────────────────────────────────────────

def test_no_with_no_pending_returns_none():
    result = resolve_inbound(_NUMBER, "NO")
    assert result is None


# ── resolver: expired confirmation ────────────────────────────────────────────

def test_expired_confirmation_cannot_be_confirmed():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    _make_confirmation(expires_at=past)
    result = resolve_inbound(_NUMBER, "YES")
    assert result is not None
    assert result.handled is True
    assert "expired" in result.reply.lower()


def test_expired_confirmation_status_is_expired():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    c = _make_confirmation(expires_at=past)
    resolve_inbound(_NUMBER, "YES")
    # The confirmation should now be resolved as expired
    resolved = store._store.get(c.confirmation_id)
    assert resolved.status == ConfirmationStatus.expired


def test_expired_no_pending_after_expiry_resolution():
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    _make_confirmation(expires_at=past)
    resolve_inbound(_NUMBER, "YES")
    assert store.get_pending(_NUMBER) is None


# ── resolver: normal message ──────────────────────────────────────────────────

def test_normal_message_returns_none():
    _make_confirmation()
    result = resolve_inbound(_NUMBER, "flights to Tokyo")
    assert result is None


def test_random_word_returns_none():
    result = resolve_inbound(_NUMBER, "hello")
    assert result is None


# ── /simulate integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_yes_with_no_pending_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "YES"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_simulate_yes_with_no_pending_reply_is_safe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "YES"},
        )
    reply = response.json()["reply"]
    assert len(reply) > 0
    assert "nothing" in reply.lower() or "waiting" in reply.lower() or "confirm" in reply.lower()


@pytest.mark.asyncio
async def test_simulate_no_with_no_pending_treated_as_normal():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/simulate",
            json={"from_number": _NUMBER, "body": "NO"},
        )
    # NO with no pending falls through to normal planner — still returns a reply
    assert response.status_code == 200
    assert len(response.json()["reply"]) > 0
