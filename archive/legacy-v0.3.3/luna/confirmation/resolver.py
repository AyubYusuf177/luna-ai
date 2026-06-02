"""
luna/confirmation/resolver.py — YES/NO confirmation resolver.

Single public function:
  resolve_inbound(user_id, body) → ResolverResult | None

Returns None when the message is not a YES/NO command, allowing normal
planner flow to continue. Returns a ResolverResult when the message
is handled by the confirmation system (even if no confirmation was pending).

Handled cases:
  - YES with a valid pending confirmation  → status=confirmed
  - YES with an expired confirmation       → status=expired, safe reply
  - YES with no pending confirmation       → safe "nothing pending" reply
  - NO with a valid or expired pending     → status=rejected
  - NO with no pending                     → None (normal flow)
"""

from datetime import datetime, timezone

from luna.confirmation import store as confirmation_store
from luna.confirmation.schemas import ConfirmationStatus, PendingConfirmation

_YES = {"yes", "y", "confirm", "ok", "okay"}
_NO = {"no", "n", "cancel", "reject"}


class ResolverResult:
    __slots__ = ("handled", "reply", "confirmation")

    def __init__(
        self,
        handled: bool,
        reply: str,
        confirmation: PendingConfirmation | None = None,
    ) -> None:
        self.handled = handled
        self.reply = reply
        self.confirmation = confirmation


def resolve_inbound(user_id: str, body: str) -> ResolverResult | None:
    """
    Check if the inbound message is a YES/NO reply to a pending confirmation.

    Returns None when body is not a YES/NO word — the runtime should
    continue with normal planner flow.
    """
    stripped = body.strip().lower()
    is_yes = stripped in _YES
    is_no = stripped in _NO

    if not is_yes and not is_no:
        return None

    pending = confirmation_store.get_pending(user_id)

    # ── YES branch ────────────────────────────────────────────────────────────

    if is_yes:
        if pending is None:
            return ResolverResult(
                handled=True,
                reply="There's nothing waiting for your confirmation right now. What would you like help with?",
            )

        now = datetime.now(timezone.utc)
        if now > pending.expires_at:
            confirmation_store.resolve(pending.confirmation_id, ConfirmationStatus.expired)
            return ResolverResult(
                handled=True,
                reply="That confirmation expired (15 min limit). Send your request again and I'll set it up fresh.",
                confirmation=pending,
            )

        confirmed = confirmation_store.resolve(pending.confirmation_id, ConfirmationStatus.confirmed)
        return ResolverResult(
            handled=True,
            reply=f"Confirmed. On it: {pending.human_summary}",
            confirmation=confirmed,
        )

    # ── NO branch ─────────────────────────────────────────────────────────────

    if pending is None:
        return None  # NO with no pending — treat as normal conversation

    now = datetime.now(timezone.utc)
    if now > pending.expires_at:
        confirmation_store.resolve(pending.confirmation_id, ConfirmationStatus.expired)
    else:
        confirmation_store.resolve(pending.confirmation_id, ConfirmationStatus.rejected)

    return ResolverResult(
        handled=True,
        reply="Cancelled. Let me know what else I can help with.",
        confirmation=pending,
    )
