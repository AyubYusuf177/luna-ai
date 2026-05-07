"""
Tests for v0.0.7 — Response Composer.

Covers:
  - Short reply passes through unchanged.
  - Long reply is truncated to ≤ 280 characters.
  - Reply with 4+ numbered options is trimmed to 3.
  - requires_confirmation=True adds YES and NO to reply_commands.
  - Policy rewrite is applied when policy_decision.allowed=False.
  - Returns a ComposedResponse instance.
  - Correct flags are set for each rule that fires.
"""

from luna.agent.schemas import RiskLevel
from luna.composer.response_composer import compose
from luna.composer.schemas import ComposedResponse
from luna.policy.schemas import PolicyDecision

_SHORT = "Here are flights from London to Tokyo. Which date works?"
_LONG = "A" * 300


# ── Basic round-trip ──────────────────────────────────────────────────────────

def test_compose_returns_composed_response():
    result = compose(_SHORT)
    assert isinstance(result, ComposedResponse)


def test_compose_short_reply_body_unchanged():
    result = compose(_SHORT)
    assert result.body == _SHORT


def test_compose_short_reply_no_flags():
    result = compose(_SHORT)
    assert result.flags == []


def test_compose_short_reply_no_commands():
    result = compose(_SHORT)
    assert result.reply_commands == []


# ── Length cap ────────────────────────────────────────────────────────────────

def test_compose_long_reply_body_within_limit():
    result = compose(_LONG)
    assert len(result.body) <= 280


def test_compose_long_reply_ends_with_ellipsis():
    result = compose(_LONG)
    assert result.body.endswith("…")


def test_compose_long_reply_sets_truncated_flag():
    result = compose(_LONG)
    assert "truncated" in result.flags


def test_compose_exactly_280_chars_not_truncated():
    body = "B" * 280
    result = compose(body)
    assert "truncated" not in result.flags
    assert len(result.body) == 280


# ── Option cap ────────────────────────────────────────────────────────────────

_FOUR_OPTIONS = (
    "Here are some options:\n"
    "1. Option Alpha — £100\n"
    "2. Option Beta — £120\n"
    "3. Option Gamma — £90\n"
    "4. Option Delta — £80"
)

_THREE_OPTIONS = (
    "Here are some options:\n"
    "1. Option Alpha — £100\n"
    "2. Option Beta — £120\n"
    "3. Option Gamma — £90"
)


def test_compose_four_options_trimmed_to_three():
    result = compose(_FOUR_OPTIONS)
    assert "4." not in result.body
    assert "Option Delta" not in result.body


def test_compose_three_options_preserved():
    result = compose(_THREE_OPTIONS)
    assert "Option Gamma" in result.body


def test_compose_four_options_sets_options_trimmed_flag():
    result = compose(_FOUR_OPTIONS)
    assert "options_trimmed" in result.flags


def test_compose_three_options_no_trimmed_flag():
    result = compose(_THREE_OPTIONS)
    assert "options_trimmed" not in result.flags


def test_compose_options_still_has_first_three():
    result = compose(_FOUR_OPTIONS)
    assert "Option Alpha" in result.body
    assert "Option Beta" in result.body
    assert "Option Gamma" in result.body


# ── Confirmation injection ────────────────────────────────────────────────────

def test_compose_requires_confirmation_adds_yes_command():
    result = compose(_SHORT, requires_confirmation=True)
    assert "YES" in result.reply_commands


def test_compose_requires_confirmation_adds_no_command():
    result = compose(_SHORT, requires_confirmation=True)
    assert "NO" in result.reply_commands


def test_compose_requires_confirmation_body_contains_yes():
    result = compose(_SHORT, requires_confirmation=True)
    assert "YES" in result.body


def test_compose_requires_confirmation_body_contains_no():
    result = compose(_SHORT, requires_confirmation=True)
    assert "NO" in result.body


def test_compose_no_confirmation_no_commands():
    result = compose(_SHORT, requires_confirmation=False)
    assert result.reply_commands == []


# ── Policy rewrite ────────────────────────────────────────────────────────────

_BLOCKED_DECISION = PolicyDecision(
    allowed=False,
    reason="Fake booking claim",
    risk_level=RiskLevel.high,
    rewritten_reply="I found great options. Tap the link to book securely.",
)

_ALLOWED_DECISION = PolicyDecision(
    allowed=True,
    risk_level=RiskLevel.low,
)


def test_compose_applies_policy_rewrite_when_blocked():
    result = compose("I booked your flight!", policy_decision=_BLOCKED_DECISION)
    assert result.body == _BLOCKED_DECISION.rewritten_reply


def test_compose_sets_policy_rewritten_flag():
    result = compose("I booked your flight!", policy_decision=_BLOCKED_DECISION)
    assert "policy_rewritten" in result.flags


def test_compose_does_not_rewrite_when_policy_allowed():
    result = compose(_SHORT, policy_decision=_ALLOWED_DECISION)
    assert result.body == _SHORT
    assert "policy_rewritten" not in result.flags


def test_compose_does_not_rewrite_when_no_policy_decision():
    result = compose(_SHORT, policy_decision=None)
    assert result.body == _SHORT


def test_compose_policy_blocked_with_no_rewrite_uses_original():
    decision = PolicyDecision(allowed=False, reason="test", risk_level=RiskLevel.low)
    result = compose(_SHORT, policy_decision=decision)
    assert result.body == _SHORT
