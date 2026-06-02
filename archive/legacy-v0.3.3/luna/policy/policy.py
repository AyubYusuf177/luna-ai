"""
luna/policy/policy.py — Inbound and outbound safety checks.

Two public functions:
  check_inbound(body)  → PolicyDecision  (user → Luna)
  check_outbound(reply) → PolicyDecision (Luna → user)

check_inbound detects:
  - STOP / START channel commands (early exit, no further processing)
  - Passport / national ID keywords or patterns
  - Card numbers (16-digit pattern)
  - Payment keywords (CVV, IBAN, bank account, etc.)

check_outbound detects:
  - Fake booking claims ("I booked it", "your booking is confirmed", etc.)
    unless a real booking event has been confirmed by the system.

Hard blocks are never configurable. The rewritten_reply field contains
the safe SMS response to send instead.
"""

import re

from luna.agent.schemas import RiskLevel
from luna.policy.schemas import PolicyDecision

# ── STOP / START word sets (exact whole-message match, case-insensitive) ─────

_STOP_WORDS = {"stop", "unsubscribe", "cancel", "quit", "end"}
_START_WORDS = {"start", "subscribe", "unstop", "begin"}

# ── Inbound sensitive-data detection ─────────────────────────────────────────

_PASSPORT_KW = [
    "passport", "national id", "id number", "social security",
    "ssn", "nin", "identity card",
]
_PAYMENT_KW = [
    "cvv", "cvc", "cvv2", "bank account", "iban",
    "sort code", "routing number", "card number",
]

# 16-digit card numbers with optional spaces or dashes
_CARD_NUMBER_RE = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')

# ── Outbound fake-booking detection ──────────────────────────────────────────

_FAKE_BOOKING_RES = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bi\s+booked\b",
        r"\byour\s+booking\s+is\s+confirmed\b",
        r"\bbooking\s+confirmed\b",
        r"i'?ve\s+booked",
        r"\bsuccessfully\s+booked\b",
        r"\byour\s+reservation\s+is\s+confirmed\b",
        r"\breservation\s+confirmed\b",
    ]
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _kw_match(text: str, keywords: list[str]) -> bool:
    """
    Return True if any keyword appears as a whole word or phrase in text.

    Uses \b word boundaries so short abbreviations like 'nin' or 'ssn'
    don't false-positive on words like 'happening' or 'lesson'.
    """
    return any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in keywords)


# ── Public API ────────────────────────────────────────────────────────────────

def check_inbound(body: str) -> PolicyDecision:
    """
    Check an inbound user message for STOP/START commands or sensitive data.

    Returns allowed=False with a rewritten_reply for any hard block.
    command="stop" or "start" signals the runtime to handle early.
    """
    stripped = body.strip().lower()

    if stripped in _STOP_WORDS:
        return PolicyDecision(
            allowed=False,
            reason="STOP command",
            risk_level=RiskLevel.low,
            command="stop",
            rewritten_reply="You've been unsubscribed from Luna. Reply START to opt back in.",
        )

    if stripped in _START_WORDS:
        return PolicyDecision(
            allowed=True,
            reason="START command",
            risk_level=RiskLevel.low,
            command="start",
            rewritten_reply=(
                "Welcome back! I'm Luna, your SMS travel assistant. "
                "What trip can I help you plan?"
            ),
        )

    if _kw_match(stripped, _PASSPORT_KW):
        return PolicyDecision(
            allowed=False,
            reason="Passport or national ID data detected in user message",
            risk_level=RiskLevel.high,
            rewritten_reply=(
                "I never collect passport or ID details over SMS. "
                "Your travel documents stay private."
            ),
        )

    if _CARD_NUMBER_RE.search(stripped):
        return PolicyDecision(
            allowed=False,
            reason="Card number pattern detected in user message",
            risk_level=RiskLevel.high,
            rewritten_reply=(
                "I never collect payment details over SMS. "
                "Use a secure checkout link for any payments."
            ),
        )

    if _kw_match(stripped, _PAYMENT_KW):
        return PolicyDecision(
            allowed=False,
            reason="Payment keyword detected in user message",
            risk_level=RiskLevel.high,
            rewritten_reply=(
                "I never collect card or bank details over SMS. "
                "Use a secure checkout link for any payments."
            ),
        )

    return PolicyDecision(allowed=True, risk_level=RiskLevel.low)


def check_outbound(reply: str) -> PolicyDecision:
    """
    Check an outbound reply for fake booking claims.

    Luna must never claim a booking is complete unless an executed booking
    event has been confirmed by the system. This function catches cases
    where a reply draft slips through with such a claim.
    """
    for pattern in _FAKE_BOOKING_RES:
        if pattern.search(reply):
            return PolicyDecision(
                allowed=False,
                reason="Reply claims a booking was completed without a confirmed booking event",
                risk_level=RiskLevel.high,
                rewritten_reply=(
                    "I found some great options. "
                    "Tap the booking link to complete your reservation securely."
                ),
            )

    return PolicyDecision(allowed=True, risk_level=RiskLevel.low)
