"""
Smoke tests — health endpoint and project structure.

Confirms the FastAPI app starts, /health returns 200 with the
expected JSON body, and the demo script exists.
"""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from luna.main import app

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


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


@pytest.mark.asyncio
async def test_health_returns_version_022():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.json()["version"] == "0.2.2"


def test_demo_script_exists():
    assert (_SCRIPTS_DIR / "demo_local.sh").exists()
