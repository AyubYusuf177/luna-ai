"""
luna/composer/response_composer.py — SMS Response Composer.

Single public function:
  compose(reply, policy_decision, requires_confirmation) → ComposedResponse

Applied rules (in order):
  1. Policy rewrite  — use rewritten_reply if policy blocked the original.
  2. Option cap      — trim numbered/bulleted list items to max 3.
  3. Confirmation    — append "Reply YES to confirm or NO to cancel." and
                       populate reply_commands when requires_confirmation=True.
  4. Length cap      — truncate to _TARGET_LENGTH chars with ellipsis.

flags field records which rules fired: policy_rewritten, options_trimmed, truncated.
reply_commands lists valid one-word commands the user can send in reply.
"""

import re

from luna.composer.schemas import ComposedResponse
from luna.policy.schemas import PolicyDecision

_TARGET_LENGTH = 280
_CONFIRMATION_SUFFIX = "\nReply YES to confirm or NO to cancel."

# Matches lines that are numbered (1. or 1)) or bulleted (- * •)
_OPTION_LINE_RE = re.compile(r"^\s*(\d+[\.\)]|\-|\*|\•)\s+")


def compose(
    reply: str,
    policy_decision: PolicyDecision | None = None,
    requires_confirmation: bool = False,
) -> ComposedResponse:
    """
    Format a raw reply for SMS delivery.

    policy_decision: pass the outbound PolicyDecision when its allowed=False
                     to apply the rewritten_reply.
    requires_confirmation: when True, appends a YES/NO prompt and populates
                           reply_commands.
    """
    flags: list[str] = []
    reply_commands: list[str] = []

    # Rule 1: policy rewrite
    if policy_decision and not policy_decision.allowed and policy_decision.rewritten_reply:
        body = policy_decision.rewritten_reply
        flags.append("policy_rewritten")
    else:
        body = reply

    # Rule 2: option cap
    body, trimmed = _limit_options(body, max_options=3)
    if trimmed:
        flags.append("options_trimmed")

    # Rule 3: confirmation suffix
    if requires_confirmation:
        candidate = body + _CONFIRMATION_SUFFIX
        if len(candidate) <= _TARGET_LENGTH:
            body = candidate
        reply_commands = ["YES", "NO"]

    # Rule 4: length cap
    if len(body) > _TARGET_LENGTH:
        body = body[: _TARGET_LENGTH - 1] + "…"
        flags.append("truncated")

    return ComposedResponse(body=body, reply_commands=reply_commands, flags=flags)


def _limit_options(body: str, max_options: int = 3) -> tuple[str, bool]:
    """Trim any numbered/bulleted list beyond max_options items."""
    lines = body.split("\n")
    option_count = 0
    result: list[str] = []
    trimmed = False

    for line in lines:
        if _OPTION_LINE_RE.match(line):
            option_count += 1
            if option_count > max_options:
                trimmed = True
                continue
        result.append(line)

    return "\n".join(result).strip(), trimmed
