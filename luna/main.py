"""
luna/main.py — FastAPI application entry point.

Registers all routes and starts the server.
In later milestones this will also register the APScheduler lifespan
and wire the Twilio webhook routes from luna.gateway.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Luna AI",
    description="SMS-native agentic travel assistant",
    version="0.0.1",
)


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness check. Returns 200 when the server is running."""
    return {"status": "ok", "version": "0.0.1"}
