"""
orchestrator — Core runtime loop.

Responsibilities (implemented from v0.0.2):
- Execute the 11-step runtime loop on every inbound event.
- Steps: identify_user → load_memory → route_workflow → advance_state
         → plan_next_step → execute_action → safety_check
         → compose_response → log_event → persist_memory → send_sms.
- Coordinate all other packages (memory, workflow, reasoning, tools,
  confirmation, composer, safety, events) without owning their logic.
- Remain stateless itself — all state lives in memory and workflow stores.
- Handle routing to the pending confirmation resolver when the inbound
  message is a YES/NO against an active confirmation object.
"""
