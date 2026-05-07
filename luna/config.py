"""
luna/config.py — Application settings.

Single source of truth for all environment-driven configuration.
Reads from .env file automatically (silently ignored if absent).
All values have safe defaults so the app starts with no .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Twilio — filled in before v0.0.3 real SMS testing
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # When True, every inbound /twilio/sms request must carry a valid
    # X-Twilio-Signature header. Set False locally and in tests.
    twilio_validate_signatures: bool = False

    # Anthropic — filled in before v0.0.4
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    # Set true only when ANTHROPIC_API_KEY is also set. False in all tests.
    use_claude_planner: bool = False

    # Scheduler — used from v0.0.8
    scheduler_poll_interval_seconds: int = 120

    # Storage backend — used from v0.0.6
    storage_backend: str = "memory"
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",       # silently ignore unknown env vars
    )


# Module-level singleton — import this everywhere.
# In tests, mutate attributes directly or use monkeypatch.
settings = Settings()
