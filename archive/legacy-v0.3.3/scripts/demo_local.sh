#!/usr/bin/env bash
# scripts/demo_local.sh — Luna AI local demo runner (v0.1.0)
#
# Runs a sequence of demo calls against a locally running server.
# Start the server first:
#   source .venv/bin/activate
#   uvicorn luna.main:app --reload
#
# Then in another terminal:
#   bash scripts/demo_local.sh

BASE="${LUNA_BASE_URL:-http://localhost:8000}"
BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
RESET="\033[0m"

section() {
    echo ""
    echo -e "${BOLD}${CYAN}── $1 ──────────────────────────────────────${RESET}"
}

run() {
    local label="$1"
    shift
    echo -e "${GREEN}> $label${RESET}"
    curl -s -X "$@" | python3 -m json.tool 2>/dev/null || true
    echo ""
}

# ── Preflight ─────────────────────────────────────────────────────────────────

if ! curl -sf "$BASE/health" > /dev/null 2>&1; then
    echo "Server not running at $BASE"
    echo "Start it with: uvicorn luna.main:app --reload"
    exit 1
fi

echo ""
echo -e "${BOLD}Luna AI — Local Demo (v0.1.0)${RESET}"
echo "Server: $BASE"

# ── A. Health check ───────────────────────────────────────────────────────────

section "A. Health check"
run "GET /health" GET "$BASE/health"

# ── B. Weather query ──────────────────────────────────────────────────────────

section "B. Weather query"
run "POST /simulate — weather in Rome" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900001", "body": "what is the weather in Rome next week"}'

# ── C. Flight search ──────────────────────────────────────────────────────────

section "C. Flight search"
run "POST /simulate — flights from London to Tokyo" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900002", "body": "find flights from London to Tokyo in October"}'

# ── D. Hotel search ───────────────────────────────────────────────────────────

section "D. Hotel search"
run "POST /simulate — hotels in Barcelona" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900003", "body": "find hotels in Barcelona for a weekend"}'

# ── E. Events search ──────────────────────────────────────────────────────────

section "E. Events search"
run "POST /simulate — events in Switzerland" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900004", "body": "what events are happening in Switzerland next month"}'

# ── F. Safety flows ───────────────────────────────────────────────────────────

section "F. Safety — STOP"
run "POST /simulate — STOP" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900005", "body": "STOP"}'

section "F. Safety — START"
run "POST /simulate — START" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900005", "body": "START"}'

section "F. Safety — YES with no pending"
run "POST /simulate — YES (no open confirmation)" \
    POST "$BASE/simulate" \
    -H "Content-Type: application/json" \
    -d '{"from_number": "+447700900005", "body": "YES"}'

# ── G. Proactive engine ───────────────────────────────────────────────────────

section "G. Proactive engine — price drop"
run "POST /simulate/proactive — price drop alert" \
    POST "$BASE/simulate/proactive" \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": "+447700900006",
      "trigger_type": "price_drop",
      "message": "Tokyo is looking unusually cheap for your October window — found a £499 return from London. Want me to compare it with 2 better-timed options?",
      "send_window_start": 0,
      "send_window_end": 24
    }'

section "G. Proactive engine — opted out (suppressed)"
run "POST /simulate/proactive — opted out" \
    POST "$BASE/simulate/proactive" \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": "+447700900007",
      "trigger_type": "check_in_reminder",
      "message": "Your check-in at Hotel Casa opens tomorrow at 15:00.",
      "opted_out": true,
      "send_window_start": 0,
      "send_window_end": 24
    }'

echo ""
echo -e "${BOLD}Demo complete.${RESET}"
echo "Open http://localhost:8000/docs for interactive API docs."
echo ""
