#!/usr/bin/env bash
# scripts/twilio_local.sh — Luna AI local Twilio SMS testing helper (v0.1.1)
#
# Checks whether the Luna server and ngrok are running, then prints the
# exact webhook URL to paste into the Twilio Console.
#
# Usage:
#   bash scripts/twilio_local.sh
#
# Prerequisites:
#   1. Luna server running:  uvicorn luna.main:app --reload
#   2. ngrok running:        ngrok http 8000

PORT="${APP_PORT:-8000}"
BOLD="\033[1m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}Luna AI — Twilio Local Testing Setup (v0.1.1)${RESET}"
echo "─────────────────────────────────────────────"

# ── 1. Luna server ────────────────────────────────────────────────────────────

if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
    VERSION=$(curl -s "http://localhost:$PORT/health" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null)
    echo -e "${GREEN}✓ Luna server${RESET} is running on port $PORT (v$VERSION)"
else
    echo -e "${RED}✗ Luna server${RESET} is NOT running on port $PORT"
    echo -e "  Start it: ${CYAN}uvicorn luna.main:app --reload${RESET}"
fi

# ── 2. ngrok ──────────────────────────────────────────────────────────────────

NGROK_URL=""
if curl -sf "http://localhost:4040/api/tunnels" > /dev/null 2>&1; then
    NGROK_URL=$(curl -s "http://localhost:4040/api/tunnels" \
        | python3 -c "
import sys, json
tunnels = json.load(sys.stdin).get('tunnels', [])
https = [t for t in tunnels if t.get('proto') == 'https']
print(https[0]['public_url'] if https else '')
" 2>/dev/null)
fi

if [ -n "$NGROK_URL" ]; then
    echo -e "${GREEN}✓ ngrok${RESET} is running: $NGROK_URL"
    WEBHOOK_URL="$NGROK_URL/twilio/sms"
    echo ""
    echo -e "${BOLD}Set this URL in Twilio Console → Phone Numbers → Webhooks:${RESET}"
    echo -e "  ${CYAN}$WEBHOOK_URL${RESET}"
    echo ""
    echo -e "${BOLD}Verify the webhook endpoint:${RESET}"
    echo -e "  ${CYAN}curl -s $NGROK_URL/health${RESET}"
else
    echo -e "${RED}✗ ngrok${RESET} is NOT running (or not on port 4040)"
    echo -e "  Start it: ${CYAN}ngrok http $PORT${RESET}"
    echo ""
    echo -e "${YELLOW}Once ngrok is running, re-run this script to get the webhook URL.${RESET}"
fi

# ── 3. Twilio Console reminder ────────────────────────────────────────────────

echo ""
echo -e "${BOLD}Twilio Console checklist:${RESET}"
echo "  https://console.twilio.com/us1/develop/phone-numbers/manage/incoming"
echo "  → Select your number"
echo "  → Messaging → 'A Message Comes In'"
echo "  → Webhook: POST  <ngrok-url>/twilio/sms"
echo ""
echo -e "${BOLD}Troubleshooting:${RESET}"
echo "  Port in use:      lsof -ti :$PORT | xargs kill -9"
echo "  ngrok URL reset:  Update webhook URL in Twilio Console after each ngrok restart"
echo "  Signature errors: Set TWILIO_VALIDATE_SIGNATURES=false in .env for local dev"
echo "  No reply sent:    Check ngrok web UI → http://localhost:4040 for request logs"
echo ""
