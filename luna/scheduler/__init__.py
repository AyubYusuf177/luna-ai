"""
scheduler — Proactive decision engine and background jobs.

Responsibilities (implemented from v0.0.8):
- Run background jobs on a configurable interval using APScheduler,
  embedded in the FastAPI process (sufficient for v0.1 single-instance).
- Jobs defined here: price_alert_check, check_in_reminder.
- Every candidate proactive message passes through the 7-check decision
  gate before being sent — the scheduler never blindly fires messages.

Decision gate (7 checks in order):
    1. SMS opt-in flag (ConsentMemory.sms_opted_in).
    2. Proactive consent flag (ConsentMemory.proactive_messages_opted_in).
    3. Recency check — no message sent in last 4 hours.
    4. Daily cap — max 1 proactive message per user per day.
    5. Pending confirmation — do not send while user has an open confirmation.
    6. Usefulness score — LLM evaluates whether message is worth sending.
    7. Time-of-day window — 08:00–21:00 in user's inferred timezone.

Outcomes: SEND | DEFER (reschedule) | SUPPRESS (log and discard).

Poll interval: SCHEDULER_POLL_INTERVAL_SECONDS env var (default 120s for demo).
"""
