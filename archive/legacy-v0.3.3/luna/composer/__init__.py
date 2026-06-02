"""
composer — Response Composer.

Responsibilities (implemented from v0.0.4):
- Post-process all LLM output into a final SMS-safe string.
- The LLM produces reasoning and structured content. The Composer
  produces the actual text the user reads. These are separate concerns.

Eight enforced rules (applied in order):
    1. Length enforcement     — target <300 chars, hard cap 320, trim + "Reply MORE".
    2. Reply command injection — every response expecting a reply has YES/NO/1/2/3/MORE.
    3. Fake booking prevention — block phrases claiming booking complete unless executed.
    4. PII echo prevention    — redact passport/card number patterns if present.
    5. Option cap             — max 3 options presented; trim + "Reply MORE for rest".
    6. Single next action     — exactly one primary call-to-action per response.
    7. Luna persona           — strip sycophantic openers (Sure!, Of course!, etc.).
    8. No apology for missing features — redirect to what Luna can do, not what she can't.

Output: ComposedResponse { body, segment_count, reply_commands, composer_flags }
"""
