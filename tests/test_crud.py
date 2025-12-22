import pytest
from httpx import AsyncClient, ASGITransport
from contacts_api.app.main import app


@pytest.mark.asyncio
async def test_create_contact(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/contacts", headers=headers, json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com"
        })
    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_get_contacts(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/contacts", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/contacts/birthdays", headers=headers)
    assert response.status_code == 200
