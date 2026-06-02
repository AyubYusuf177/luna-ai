"""
safety — Safety and policy enforcement layer.

Responsibilities (implemented from v0.0.4):
- Applied at two points in every runtime loop:
    (a) Before action execution — check Action Registry (allowed_in_v0_1).
    (b) After response composition — scan final SMS for policy violations.

Hard blocks (cannot be overridden by any config or prompt):
    - Passport / ID data collection → blocked, response rewritten.
    - Payment / card data collection → blocked, response rewritten.
    - Executing unconfirmed medium/high-risk actions → force confirmation gate.
    - Claiming a booking is complete when it is not → response rewritten.
    - STOP command → immediate opt-out, single TCPA confirmation, no further messages.

Soft checks (logged, configurable):
    - Off-topic scope (non-travel intent) → log + redirect.
    - Ambiguous YES with no pending confirmation → reject + clarify.
    - Proactive daily cap exceeded → suppress + log.
    - Workflow abandoned (48h silent) → mark ABANDONED, no re-engagement in v0.1.
"""
