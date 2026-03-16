"""
Smoke tests — run with: pytest tests/ -v
Requires: pip install pytest pytest-asyncio httpx
"""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200
    assert "version" in r.json()


@pytest.mark.asyncio
async def test_login_bad_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/v1/auth/login", json={"email": "bad@test.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_no_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/v1/users")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_openapi_spec():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/v1/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "AcademyPro API"
    # Verify key path groups exist
    paths = spec.get("paths", {})
    assert any("/auth/" in p for p in paths)
    assert any("/coaches" in p for p in paths)
    assert any("/players" in p for p in paths)
    assert any("/sessions" in p for p in paths)
    assert any("/billing/" in p for p in paths)
