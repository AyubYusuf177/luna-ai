"""
luna/main.py — FastAPI application entry point.

Registers all routers. In later milestones this will also register
the APScheduler lifespan (v0.0.8) and any startup/shutdown hooks.
"""

from fastapi import FastAPI

from luna.gateway.router import router as gateway_router

app = FastAPI(
    title="Luna AI",
    description="SMS-native agentic travel assistant",
    version="0.0.2",
)

app.include_router(gateway_router)


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness check. Returns 200 when the server is running."""
    return {"status": "ok", "version": "0.0.2"}
