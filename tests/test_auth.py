import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from contacts_api.app.main import app

@pytest.mark.asyncio
async def test_signup_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "string123"
        })
    assert response.status_code == 201
    assert response.json()["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # ensure user exists
        await ac.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "string123"
        })

        response = await ac.post(
            "/api/auth/login",
            data={"email": "test@example.com", "password": "string123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # ensure user exists
        await ac.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "string123"
        })

        response = await ac.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_profile_success(auth_user):
    headers = {"Authorization": f"Bearer {auth_user['token']}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == auth_user["email"]


@pytest.mark.asyncio
async def test_get_my_profile_unauthorized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_signup_conflict(client):
    email = "dup@example.com"
    await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    r = await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    r = await client.post("/api/auth/login", json={"email": "nope@example.com", "password": "wrong123"})
    assert r.status_code == 401
from contacts_api.app.jwt_utils import create_email_token

@pytest.mark.asyncio
async def test_verify_email_user_not_found(client):
    token = create_email_token("ghost@example.com")
    r = await client.get(f"/api/auth/verify-email/{token}")
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_verify_email_success(client):
    email = "v@example.com"
    await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    token = create_email_token(email)
    r = await client.get(f"/api/auth/verify-email/{token}")
    assert r.status_code == 200
