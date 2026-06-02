"""
luna/channels/schemas.py — Raw channel payload schemas.

These document the exact shape of what each channel source delivers
before normalization. They are NOT used downstream of the Event Gateway.

Keeping them here makes it easy to update when a channel's API changes
without touching the rest of the codebase.
"""

from pydantic import BaseModel


class TwilioSMSPayload(BaseModel):
    """
    Subset of fields Twilio sends in a webhook POST (form-encoded).

    Full field reference: https://www.twilio.com/docs/sms/twiml#request-parameters
    Only the fields Luna uses are declared; extras are allowed via model_config.
    """

    From: str           # Sender's E.164 phone number
    Body: str           # Message text
    MessageSid: str = ""
    AccountSid: str = ""
    To: str = ""        # Luna's Twilio number
    FromCountry: str = ""
    ToCountry: str = ""

    class Config:
        extra = "allow"  # Twilio sends many fields; ignore the rest silently
