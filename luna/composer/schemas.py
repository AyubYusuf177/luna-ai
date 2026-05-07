"""luna/composer/schemas.py — ComposedResponse schema."""

from pydantic import BaseModel


class ComposedResponse(BaseModel):
    body: str
    reply_commands: list[str] = []
    flags: list[str] = []
