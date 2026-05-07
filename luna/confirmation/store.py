"""
luna/confirmation/store.py — In-memory pending confirmation store.

Rules enforced here:
  - Only one pending confirmation per user at a time.
  - Creating a second confirmation for the same user silently replaces the first.
  - TTL defaults to 15 minutes; tests may override expires_at directly.

Public interface:
  create(user_id, task_id, action_type, human_summary, ...) → PendingConfirmation
  get_pending(user_id)                                       → PendingConfirmation | None
  resolve(confirmation_id, status)                           → PendingConfirmation | None
  reset()                                                    → None  [tests only]
"""

from datetime import datetime, timedelta, timezone

from luna.agent.schemas import RiskLevel
from luna.confirmation.schemas import ConfirmationStatus, PendingConfirmation

_DEFAULT_TTL_MINUTES = 15

# confirmation_id → PendingConfirmation
_store: dict[str, PendingConfirmation] = {}
# user_id → active confirmation_id (the one pending confirmation per user)
_user_pending: dict[str, str] = {}


def create(
    user_id: str,
    task_id: str,
    action_type: str,
    human_summary: str,
    structured_payload: dict | None = None,
    risk_level: RiskLevel = RiskLevel.medium,
    ttl_minutes: int = _DEFAULT_TTL_MINUTES,
    expires_at: datetime | None = None,
) -> PendingConfirmation:
    """
    Create a pending confirmation for a user.

    Replaces any existing pending confirmation for that user.
    Pass expires_at explicitly in tests to simulate expiry.
    """
    now = datetime.now(timezone.utc)
    confirmation = PendingConfirmation(
        user_id=user_id,
        task_id=task_id,
        action_type=action_type,
        human_summary=human_summary,
        structured_payload=structured_payload or {},
        risk_level=risk_level,
        created_at=now,
        expires_at=expires_at or (now + timedelta(minutes=ttl_minutes)),
    )
    _store[confirmation.confirmation_id] = confirmation
    _user_pending[user_id] = confirmation.confirmation_id
    return confirmation


def get_pending(user_id: str) -> PendingConfirmation | None:
    """Return the active pending confirmation for user_id, or None."""
    cid = _user_pending.get(user_id)
    if cid is None:
        return None
    return _store.get(cid)


def resolve(
    confirmation_id: str,
    status: ConfirmationStatus,
) -> PendingConfirmation | None:
    """
    Set the status of a confirmation and remove it from the pending index.
    Returns None if the confirmation_id is not found.
    """
    confirmation = _store.get(confirmation_id)
    if confirmation is None:
        return None
    confirmation.status = status
    _user_pending.pop(confirmation.user_id, None)
    return confirmation


def reset() -> None:
    """Clear all confirmation state. Call from test fixtures only."""
    _store.clear()
    _user_pending.clear()
