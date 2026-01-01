import pytest
from httpx import ASGITransport, AsyncClient
from contacts_api.app.main import app

@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    await client.post("/api/auth/signup", json={
        "email": "dup@example.com",
        "password": "string123",
    })
    r = await client.post("/api/auth/signup", json={
        "email": "dup@example.com",
        "password": "string123",
    })
    assert r.status_code in (400, 409)


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/signup", json={
        "email": "u2@example.com",
        "password": "string123",
    })
    r = await client.post("/api/auth/login", json={
        "email": "u2@example.com",
        "password": "wrong",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client):
    r = await client.post(
        "/api/auth/reset-password/invalid",
        json="newpass123",  # <- body як string, не {"password": ...}
    )
    assert r.status_code == 400
