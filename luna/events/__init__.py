"""
events — Event logger.

Responsibilities (implemented from v0.0.2):
- Append-only event log. Never updates or deletes entries.
- Every meaningful step in the runtime loop writes an event.
- v0.1 backend: in-memory list. Future: SQLite / PostgreSQL with
  90-day rolling retention for non-PII events.

Event types logged:
    Inbound:       inbound_sms_received, proactive_trigger_evaluated
    User:          user_identified, user_profile_updated,
                   opt_out_received, opt_in_received
    Workflow:      workflow_created, workflow_state_transitioned,
                   workflow_completed, workflow_failed,
                   workflow_abandoned, workflow_cancelled
    Tools:         tool_called, tool_succeeded, tool_failed
    Confirmation:  confirmation_created, confirmation_accepted,
                   confirmation_rejected, confirmation_expired
    Safety:        safety_violation_blocked, scope_violation_logged,
                   ambiguous_confirmation_logged, pii_block_triggered
    Outbound:      outbound_sms_sent, proactive_message_sent,
                   proactive_message_suppressed, proactive_message_deferred

Schema: { event_id, user_id, workflow_id, event_type, timestamp, metadata, session_id }
"""
