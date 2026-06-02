"""
confirmation — Pending confirmation store and resolver.

Responsibilities (implemented from v0.0.6):
- Store Confirmation objects for any action with risk_level medium or high.
- Enforce the one-active-confirmation-per-user rule at all times.
- Resolve YES/NO replies against the specific pending Confirmation object.
- Expire confirmations after 15 minutes (v0.1 default).
- Reject stale YES replies against expired confirmations gracefully.

Confirmation schema:
    confirmation_id     — UUID
    user_id             — string (phone number)
    workflow_id         — UUID
    action_type         — string (from action registry)
    human_summary       — plain English description shown to user
    structured_payload  — exact parameters the action will use on confirm
    risk_level          — medium | high
    created_at          — datetime
    expires_at          — datetime (created_at + 15 minutes)
    status              — pending | confirmed | rejected | expired

A user replying YES must resolve a specific pending Confirmation by ID,
not a vague previous message. Ambiguous YES with no pending confirmation
is rejected with a clarifying message.
"""
