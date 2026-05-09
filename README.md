# Luna AI

Luna is an SMS-native agentic travel operator.

Luna is not a chatbot. Luna is a persistent travel operator that lives inside SMS — it remembers context across messages, manages multi-step travel workflows, enforces safety and consent policies, and proactively reaches out when something relevant happens (a price drop, a check-in window opening, a weather change). The user never has to visit a website or app.

---

## What Luna is not yet

Luna v0.1.0 is a demo-ready foundation. The following are intentionally out of scope until later phases:

- **No real bookings.** Flight, hotel, and event searches return mock data.
- **No real APIs.** No Amadeus, Duffel, Booking.com, or Skyscanner integration.
- **No payments.** No Stripe, no card collection, no transactions.
- **No passport or ID collection.**
- **No WhatsApp or web chat.** SMS only (Twilio, configurable).
- **No frontend UI.** Luna is accessed entirely through SMS.
- **No real background scheduler.** The proactive engine exists and is fully testable via `/simulate/proactive`. APScheduler background jobs are not wired into the FastAPI lifespan yet.
- **No multi-agent orchestration.** One agent, one runtime loop per message.

---

## Architecture

```
luna/
├── main.py             FastAPI entry point + lifespan (backend init)
├── config.py           pydantic-settings config (env vars)
│
├── gateway/            HTTP routes + InternalEvent schema
│   ├── router.py         /simulate, /simulate/proactive, /twilio/sms
│   ├── event_gateway.py  Normalises all channel input → agent runtime
│   └── schemas.py        InternalEvent, SimulateRequest/Response, ...
│
├── channels/           Channel adapters (thin normalisers)
│   ├── simulator.py      POST /simulate → InternalEvent
│   └── twilio.py         Twilio webhook → InternalEvent + outbound send
│
├── agent/              Core agent loop
│   ├── runtime.py        13-step request handler
│   ├── task_manager.py   Create / read / update TravelTask
│   └── schemas.py        TravelTask, TaskPattern, PlannerOutput, ...
│
├── reasoning/          Planner
│   └── planner.py        Fallback (keyword/regex) + optional Claude planner
│
├── tools/              Tool layer
│   ├── registry.py       Named ToolDefinition registry
│   ├── dispatcher.py     Routes ToolRequest → ToolResult, never raises
│   └── mock/             weather_lookup, flight_search, hotel_search, events_search
│
├── memory/             Persistence
│   ├── backend.py        Module-level active backend + init_backend()
│   ├── store.py          User + conversation API (delegates to backend)
│   └── backends/
│       ├── in_memory.py  Default (tests + dev, no disk writes)
│       └── sqlite.py     Persistent (survives restarts)
│
├── policy/             Inbound + outbound safety checks
│   └── policy.py         STOP/START, PII blocking, fake-booking detection
│
├── composer/           SMS response formatting
│   └── response_composer.py  Policy rewrite → option cap → confirm suffix → 280-char cap
│
├── confirmation/       User confirmation gate
│   ├── store.py          One pending confirmation per user (15-min TTL)
│   └── resolver.py       YES / NO → confirm / reject / expire
│
├── scheduler/          Proactive engine
│   ├── schemas.py        TriggerType, ProactiveCandidate, ProactiveDecision
│   ├── proactive_engine.py  6-check decision gate
│   └── jobs.py           build_message(), create_scheduler_event()
│
└── events/             Append-only event log
    └── logger.py         log(), get_log() — backed by active memory backend
```

### Request flow (inbound SMS)

```
Twilio / /simulate
      ↓
  channel adapter  →  InternalEvent
      ↓
  event_gateway.handle(event)
      ↓
  agent/runtime.py — 13 steps:
    1. Log inbound event
    2. Identify / create user
    3. Append inbound conversation turn
    4. policy.check_inbound  →  STOP/START  →  early return
    5. policy blocked (PII)  →  early return
    6. confirmation_resolver →  YES/NO      →  early return
    7. List active tasks for user
    8. Plan (fallback or Claude): TravelTask + PlannerOutput
    9. Create or update TravelTask
   10. Dispatch tool if selected
   11. policy.check_outbound on raw reply
   12. composer.compose (rewrite → options → confirm suffix → truncate)
   13. Append outbound turn, log, return
```

### Proactive engine decision gate

```
ProactiveCandidate
      ↓
  1. opted_out=True          →  SUPPRESS (user_opted_out)
  2. proactive_opt_in=False  →  SUPPRESS (proactive_not_opted_in)
  3. 3+ sends today          →  SUPPRESS (daily_cap_exceeded)
  4. pending confirmation    →  DEFER    (retry_at = confirmation.expires_at)
  5. outside send window     →  DEFER    (retry_at = next window open)
  6. all clear               →  SEND
```

---

## Milestone history

| Version | Description | Status |
|---------|-------------|--------|
| v0.0.1  | FastAPI skeleton, /health endpoint | ✅ Done |
| v0.0.2  | Local /simulate SMS simulator | ✅ Done |
| v0.0.3  | Channel layer + Event Gateway + Twilio webhook | ✅ Done |
| v0.0.4  | Agent Runtime kernel + TravelTask + fallback planner | ✅ Done |
| v0.0.5  | Tool Registry + mock tools (weather, flights, hotels, events) | ✅ Done |
| v0.0.6  | SQLite persistent memory (pluggable backend) | ✅ Done |
| v0.0.7  | Policy layer + Response Composer + Confirmation System | ✅ Done |
| v0.0.8  | Proactive Engine — 6-check decision gate + /simulate/proactive | ✅ Done |
| v0.1.0  | Demo-ready — hardening, README, demo script | ✅ Done |

---

## Local setup

### Prerequisites

- Python 3.11+
- Git

### 1. Clone and enter the repo

```bash
git clone <repo-url>
cd luna-ai
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

For local development and testing no values need to be filled in — the defaults use in-memory storage, the keyword/regex fallback planner, and disabled Twilio signature validation.

---

## Run the server

```bash
uvicorn luna.main:app --reload
```

The server starts at `http://localhost:8000`. Auto-reload is on.

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

---

## Run the tests

```bash
pytest -v
```

Expected: **296 passed** — no external calls, no real APIs, no real Twilio sends.

---

## Demo: example flows

### Option 1 — demo script (server must be running first)

```bash
# Terminal 1
uvicorn luna.main:app --reload

# Terminal 2
bash scripts/demo_local.sh
```

### Option 2 — manual curl commands

#### A. Health check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "version": "0.1.0"}
```

---

#### B. Weather query

```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900001", "body": "what is the weather in Rome next week"}'
```

```json
{
  "from_number": "+447700900001",
  "reply": "Rome: Sunny, high 24°C / low 14°C. Good travel weather."
}
```

---

#### C. Flight search

```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900002", "body": "find flights from London to Tokyo in October"}'
```

```json
{
  "from_number": "+447700900002",
  "reply": "Flights London→Tokyo: BA 08:00 £189 · EZY 13:30 £124. Which would you like?"
}
```

---

#### D. Hotel search

```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900003", "body": "find hotels in Barcelona for a weekend"}'
```

```json
{
  "from_number": "+447700900003",
  "reply": "Hotels in Barcelona: City Central ★★★★ £110/night · Budget Inn ★★★ £65/night. Want more details?"
}
```

---

#### E. Events search

```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900004", "body": "what events are happening in Switzerland next month"}'
```

```json
{
  "from_number": "+447700900004",
  "reply": "Events in Switzerland: Jazz Night @ The Blue Note Fri 8pm · Food Festival @ City Park Sat–Sun. Interested in either?"
}
```

---

#### F. Safety flows

**STOP:**
```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900005", "body": "STOP"}'
```
Luna replies with an opt-out confirmation. The policy layer intercepts before the agent runs.

**START:**
```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900005", "body": "START"}'
```

**YES with no pending confirmation:**
```bash
curl -s -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"from_number": "+447700900005", "body": "YES"}'
```
Luna replies with a safe message — a stray "YES" never accidentally confirms anything.

---

#### G. Proactive engine

**Price drop — send:**

```bash
curl -s -X POST http://localhost:8000/simulate/proactive \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+447700900006",
    "trigger_type": "price_drop",
    "message": "Tokyo is looking unusually cheap for your October window — found a £499 return from London. Want me to compare it with 2 better-timed options?",
    "send_window_start": 0,
    "send_window_end": 24
  }'
```

```json
{
  "decision": "send",
  "reason": "all_checks_passed",
  "message": "Price drop: Tokyo is looking unusually cheap for your October window — found a £499 return from London. Want me to compare it with 2 better-timed options?",
  "retry_at": null
}
```

**Opted out — suppress:**

```bash
curl -s -X POST http://localhost:8000/simulate/proactive \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+447700900007",
    "trigger_type": "check_in_reminder",
    "message": "Your check-in at Hotel Casa opens tomorrow at 15:00.",
    "opted_out": true,
    "send_window_start": 0,
    "send_window_end": 24
  }'
```

```json
{
  "decision": "suppress",
  "reason": "user_opted_out",
  "message": null,
  "retry_at": null
}
```

**Outside send window — defer:**

```bash
curl -s -X POST http://localhost:8000/simulate/proactive \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+447700900008",
    "trigger_type": "weather_change",
    "message": "Rain forecast in Paris this weekend — you may want waterproofs.",
    "send_window_start": 9,
    "send_window_end": 10
  }'
```

```json
{
  "decision": "defer",
  "reason": "outside_send_window",
  "message": null,
  "retry_at": "2026-05-09T09:00:00+00:00"
}
```

---

## Configuration

### Persistent memory (SQLite)

By default Luna uses in-memory storage — state resets when the server stops. To persist across restarts:

```bash
# .env
LUNA_MEMORY_BACKEND=sqlite
LUNA_DB_PATH=./data/luna.db
```

The database is created automatically. It is excluded from git by `.gitignore`.

### Claude planner

By default Luna uses a deterministic keyword/regex fallback planner. To enable real Claude planning:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
USE_CLAUDE_PLANNER=true
ANTHROPIC_MODEL=claude-sonnet-4-6
```

The Claude planner only activates when both variables are set. Tests always use the fallback — no API key is needed to run the test suite.

### Twilio SMS (real device testing)

1. Create a Twilio account at [console.twilio.com](https://console.twilio.com) and buy a number.
2. Set credentials in `.env`:

```bash
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+14155552671
```

3. Expose the local server:

```bash
ngrok http 8000
```

4. In the Twilio console, set the inbound webhook for your number:

```
POST https://<ngrok-id>.ngrok-free.app/twilio/sms
```

5. Enable signature validation in production:

```bash
TWILIO_VALIDATE_SIGNATURES=true
```

---

## Safety

Luna enforces several protection layers by default:

| Check | Behaviour |
|-------|-----------|
| STOP / UNSUBSCRIBE / CANCEL | Stops all outbound messages to that number |
| START / SUBSCRIBE / UNSTOP | Re-enables messaging |
| Passport / national ID keywords | Blocked with a privacy reply |
| Card numbers (16-digit patterns) | Blocked |
| CVV / IBAN / sort code keywords | Blocked |
| Fake booking claims in outbound | Detected and rewritten before delivery |
| Confirmation gate | High-risk actions require an explicit YES before execution |
| Reply length | Capped at 280 characters |
| Options list | Capped at 3 choices per message |
| Proactive opt-in | Proactive messages require explicit opt-in; daily cap is 3 per user |

Luna **never** collects financial data, government IDs, or booking credentials over SMS.
Luna **never** claims to have completed a booking — all bookings go via a secure handoff link (v1.x+).

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| Validation | Pydantic v2 + pydantic-settings |
| SMS channel | Twilio (optional for dev/test) |
| LLM planner | Anthropic Claude (optional, `USE_CLAUDE_PLANNER=true`) |
| Storage | In-memory (default) · SQLite (persistent) |
| Testing | pytest + pytest-asyncio |
