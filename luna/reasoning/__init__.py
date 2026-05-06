"""
reasoning — LLM interaction layer.

Responsibilities (implemented from v0.0.3):
- Wrap the Anthropic Claude API (claude-sonnet-4-6 in v0.1).
- Maintain system prompts per context type (onboarding, reactive, proactive).
- Extract structured intents and field values from user messages.
- Validate all LLM outputs against Pydantic schemas before returning.
- Plan the next_action for the active workflow (ASK_CLARIFICATION,
  CALL_TOOL, CREATE_CONFIRMATION, COMPLETE_WORKFLOW).
- Retry once with a stricter prompt if structured output validation fails.
  If it fails again, return a safe fallback (ask user to rephrase).

The LLM produces reasoning and structured output. It does NOT produce
the final SMS text directly — that is the Response Composer's job.
"""
