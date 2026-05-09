"""
luna/scheduler/proactive_engine.py — Proactive message decision gate (v0.0.8).

evaluate() runs a candidate proactive message through a 6-check gate
and returns a ProactiveDecision of SEND, DEFER, or SUPPRESS.

Decision gate (in order):
  1. opted_out=True            → suppress
  2. proactive_opt_in=False    → suppress
  3. daily cap (3/day) hit     → suppress
  4. pending confirmation open → defer until confirmation expires
  5. outside send window       → defer until window opens
  6. all clear                 → send
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from luna.confirmation import store as confirmation_store
from luna.events import logger as events
from luna.scheduler.schemas import (
    ProactiveCandidate,
    ProactiveDecision,
    ProactiveDecisionType,
)

_DAILY_CAP = 3


def evaluate(
    candidate: ProactiveCandidate,
    _current_hour: int | None = None,
) -> ProactiveDecision:
    """
    Run the proactive decision gate. Returns a ProactiveDecision.

    Pass _current_hour in tests to override the real wall-clock hour
    without mocking datetime.
    """
    # 1. SMS opt-out
    if candidate.opted_out:
        return ProactiveDecision(
            decision=ProactiveDecisionType.suppress,
            reason="user_opted_out",
            user_id=candidate.user_id,
            task_id=candidate.task_id,
        )

    # 2. Proactive opt-in
    if not candidate.proactive_opt_in:
        return ProactiveDecision(
            decision=ProactiveDecisionType.suppress,
            reason="proactive_not_opted_in",
            user_id=candidate.user_id,
            task_id=candidate.task_id,
        )

    # 3. Daily cap
    today = datetime.now(timezone.utc).date()
    sent_today = sum(
        1
        for e in events.get_log()
        if e.event_type == "proactive_sent"
        and e.user_id == candidate.user_id
        and e.timestamp.date() == today
    )
    if sent_today >= _DAILY_CAP:
        return ProactiveDecision(
            decision=ProactiveDecisionType.suppress,
            reason="daily_cap_exceeded",
            user_id=candidate.user_id,
            task_id=candidate.task_id,
        )

    # 4. Pending confirmation — do not interrupt a user mid-decision
    pending = confirmation_store.get_pending(candidate.user_id)
    if pending is not None:
        return ProactiveDecision(
            decision=ProactiveDecisionType.defer,
            reason="pending_confirmation",
            user_id=candidate.user_id,
            task_id=candidate.task_id,
            retry_at=pending.expires_at,
        )

    # 5. Time-of-day window
    now = datetime.now(timezone.utc)
    hour = _current_hour if _current_hour is not None else now.hour
    in_window = candidate.send_window_start <= hour < candidate.send_window_end
    if not in_window:
        if hour < candidate.send_window_start:
            retry_at = now.replace(
                hour=candidate.send_window_start, minute=0, second=0, microsecond=0
            )
        else:
            retry_at = (now + timedelta(days=1)).replace(
                hour=candidate.send_window_start, minute=0, second=0, microsecond=0
            )
        return ProactiveDecision(
            decision=ProactiveDecisionType.defer,
            reason="outside_send_window",
            user_id=candidate.user_id,
            task_id=candidate.task_id,
            retry_at=retry_at,
        )

    # 6. All checks passed — send
    return ProactiveDecision(
        decision=ProactiveDecisionType.send,
        reason="all_checks_passed",
        user_id=candidate.user_id,
        task_id=candidate.task_id,
        message=candidate.message,
    )
