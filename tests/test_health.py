"""
Smoke test — v0.0.1.

Confirms the FastAPI app starts and /health returns 200 with the
expected JSON body. This test must pass before any other work begins.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from luna.main import app


@pytest.mark.asyncio
async def test_health_returns_200():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_expected_body():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
