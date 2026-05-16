# Luna AI — Claude Code Project Memory

## 1. Product Identity

Luna AI is an SMS-native agentic travel operator.

- Not a chatbot.
- Not a preset workflow wizard.
- Not a normal travel app.
- SMS is the primary interface. The agent lives inside messages.
- A future web/app UI exists only for onboarding, billing, permissions, integrations, account settings, and trip review — not for travel operations.

---

## 2. Current Architecture

| Layer | Module | Role |
|---|---|---|
| Channel adapters | `luna/channels/` | Thin normalisers for each input source (`/simulate`, `/twilio/sms`) |
| Event Gateway | `luna/gateway/event_gateway.py` | Converts all channel input into a normalised `InternalEvent` |
| Agent Runtime | `luna/agent/runtime.py` | Source-agnostic 13-step processing loop |
| Planner | `luna/reasoning/planner.py` | Fallback (keyword/regex) + Claude planner (tool use) |
| TravelTask | `luna/agent/schemas.py` | Generic goal/task object with known_fields, missing_fields, tools |
| Tool Registry | `luna/tools/registry.py` | Named tool definitions; dispatcher routes calls to mock implementations |
| Memory | `luna/memory/` | `InMemoryBackend` (tests/dev) or `SQLiteBackend` (`LUNA_MEMORY_BACKEND=sqlite`) |
| Policy | `luna/policy/policy.py` | Inbound/outbound safety checks — STOP/START, PII blocking, fake-booking detection |
| Composer | `luna/composer/response_composer.py` | Policy rewrite → option cap (3) → confirm suffix → 280-char truncation |
| Confirmation | `luna/confirmation/` | One pending confirmation per user, 15-min TTL, YES/NO resolver |
| Proactive Engine | `luna/scheduler/proactive_engine.py` | 6-check gate: opted_out → opt_in → daily cap → pending confirm → send window → send |
| Event Log | `luna/events/logger.py` | Append-only audit log backed by active memory backend |

---

## 3. Completed Milestones

| Version | Description |
|---|---|
| v0.0.1 | FastAPI skeleton, `/health` endpoint |
| v0.0.2 | Local `/simulate` SMS simulator |
| v0.0.3 | Channel Layer + Event Gateway + Twilio webhook |
| v0.0.4 | Agent Runtime + TravelTask + planner interface |
| v0.0.5 | Tool Registry + mock tools (weather, flights, hotels, events) |
| v0.0.6 | SQLite persistent memory (pluggable backend) |
| v0.0.7 | Policy Layer + Response Composer + Confirmation System |
| v0.0.8 | Proactive Engine — 6-check decision gate + `/simulate/proactive` |
| v0.1.0 | Demo-ready hardening, README, demo script |
| v0.1.1 | Twilio SMS hardening — TwiML responses, ngrok guide |
| v0.2.0 | Claude-powered structured planner |

---

## 4. Current Verified State

- v0.2.0 committed and pushed to `main`. Tests: 328 passed.
- Claude planner verified with a real Anthropic API key. Three manual tests passed:
  - "somewhere warm for 4 days in June under £500, not Spain" → extracted constraints, asked for origin.
  - "I land in Rome at 9pm, find me a hotel near the station and something relaxed the next morning" → asked for arrival date and stay length.
  - "Keep an eye on Tokyo for October but only tell me if it is meaningfully cheaper than usual" → `monitor_and_alert` pattern, asked for origin.
- Twilio webhook verified through ngrok with TwiML response.
- Twilio UK SMS number compliance ticket unresolved (external blocker).

---

## 5. Planner Strategy

- **Fallback planner** — deterministic keyword/regex matching. Always present. Always used in tests. Never remove it.
- **Claude planner** — real frontier-model planning via `plan_travel_action` tool use. Active when `USE_CLAUDE_PLANNER=true` AND `ANTHROPIC_API_KEY` is set.
- Malformed Claude output triggers one retry with a repair prompt, then falls back to deterministic.
- All Claude output is Pydantic-validated as `PlannerOutput` before use.
- `_call_claude_once(client, messages)` is module-level so tests can patch it via `monkeypatch.setattr("luna.reasoning.planner._call_claude_once", mock_fn)` — no SDK mocking needed.
- Tests must never make real Anthropic API calls.

---

## 6. Tool Strategy

- Tools are Luna's hands — the way she acts on the world.
- Current tools are all mock implementations. No real external APIs yet.
- New capabilities should be added as tools in the registry, not as hardcoded logic in the runtime.
- Future tools (in rough priority order): real weather, events/places, flights, hotels, transport, calendar, booking handoff.

---

## 7. Safety Rules

These are non-negotiable. Do not weaken them.

- Never collect passport, national ID, or government ID numbers over SMS.
- Never collect card numbers, CVV, IBAN, sort codes, or any payment credentials over SMS.
- Never claim a booking is complete unless a confirmed booking event was returned.
- STOP must immediately opt the user out. START must re-enable messages.
- Medium and high-risk actions require explicit YES/NO confirmation before execution.
- Only one pending confirmation per user at a time.

---

## 8. Near-Term Roadmap

| Version | Goal |
|---|---|
| v0.2.1 | Planner Evaluation Suite — offline harness to measure and improve planner reasoning |
| v0.2.2 | Planner cost and logging controls |
| v0.3.0 | First real low-risk API tool (likely weather) |
| v0.3.1 | Real events/places tool |
| v0.4.0 | Real proactive scheduled checks |
| v0.5.0 | Web onboarding and settings UI |
| v1.0 | Real SMS beta |

Do not start any milestone without explicit approval.

---

## 9. Operating Rules for Claude Code

- Read this file at the start of every session.
- Run `git status` before making any changes.
- Read existing files before creating new ones. Do not duplicate modules.
- Do not create files that aren't needed.
- Build in small, focused milestone commits.
- Run `pytest -v` before and after any significant change.
- Never commit `.env` or any secrets.
- No real API calls in tests — mock at `_call_claude_once`, not at the SDK level.
- Do not remove the fallback planner.
- Do not build a frontend yet.
- Do not build payments, direct bookings, or passport/ID flows.
- Do not create hardcoded workflow trees for travel intent cases — use TravelTask + planner + tool registry.
- Wait for explicit approval before starting a new milestone.

---

## 10. Useful Commands

```bash
# Status
git status
git log --oneline -5

# Tests
pytest -v

# Server
uvicorn luna.main:app --reload

# Health check
curl -s http://localhost:8000/health

# Simulate inbound SMS
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700000001", "body": "find flights from London to Rome"}'

# Simulate proactive message
curl -s -X POST http://localhost:8000/simulate/proactive \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+447700000001",
    "trigger_type": "price_drop",
    "message": "Tokyo is looking cheap for October.",
    "send_window_start": 0,
    "send_window_end": 24
  }'

# ngrok tunnel (run in a separate terminal)
ngrok http 8000
# Then: bash scripts/twilio_local.sh
```
