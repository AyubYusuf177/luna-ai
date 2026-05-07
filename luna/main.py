"""
luna/main.py — FastAPI application entry point.

Registers all routers and wires up the persistence backend via lifespan.
The backend (in-memory or SQLite) is chosen from settings at startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from luna.config import settings
from luna.gateway.router import router as gateway_router
from luna.memory.backend import init_backend


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_backend(settings)
    yield


app = FastAPI(
    title="Luna AI",
    description="SMS-native agentic travel assistant",
    version="0.0.6",
    lifespan=lifespan,
)

app.include_router(gateway_router)


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness check. Returns 200 when the server is running."""
    return {"status": "ok", "version": "0.0.6"}
