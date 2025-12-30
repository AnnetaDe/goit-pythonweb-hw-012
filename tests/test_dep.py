import pytest
from httpx import AsyncClient, ASGITransport

from contacts_api.app.main import app


@pytest.mark.asyncio
async def test_protected_route_without_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
    assert r.status_code == 401
