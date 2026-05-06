"""
tests — Luna AI test suite.

Test modules map to Luna packages:
    test_health.py          — /health endpoint smoke test (v0.0.1)
    test_gateway.py         — Twilio webhook handling (v0.0.3)
    test_orchestrator.py    — Runtime loop (v0.0.2+)
    test_workflow_engine.py — Workflow creation, routing, advancement (v0.0.4)
    test_state_machines.py  — State transition validation per workflow type (v0.0.4)
    test_tools.py           — Tool dispatcher + mock tools (v0.0.5)
    test_confirmation.py    — Confirmation store + YES/NO resolver (v0.0.6)
    test_composer.py        — Response Composer rules (v0.0.4)
    test_safety.py          — Hard blocks + soft checks (v0.0.4)
    test_memory.py          — Memory segment read/write (v0.0.4)
    test_proactive_engine.py — 7-check decision gate (v0.0.8)
"""
