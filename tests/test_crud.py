import pytest
from httpx import AsyncClient, ASGITransport
from contacts_api.app.main import app


@pytest.mark.asyncio
async def test_create_contact(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/contacts/", headers=headers, json={
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
@pytest.mark.asyncio
async def test_update_contact(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post(
            "/api/contacts/",
            headers=headers,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@doe.com",
                "phone": "123",
            },
        )
        cid = create.json()["id"]

        update = await ac.put(
            f"/api/contacts/{cid}",
            headers=headers,
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@doe.com",
                "phone": "456",
            },
        )

    assert update.status_code == 200
    assert update.json()["first_name"] == "Jane"


@pytest.mark.asyncio
async def test_delete_contact(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post(
            "/api/contacts/",
            headers=headers,
            json={
                "first_name": "Del",
                "last_name": "Me",
                "email": "del@me.com",
                "phone": "999",
            },
        )
        cid = create.json()["id"]

        delete = await ac.delete(f"/api/contacts/{cid}", headers=headers)

    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_search_contacts(get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/contacts/",
            headers=headers,
            json={
                "first_name": "Alice",
                "last_name": "Wonder",
                "email": "alice@wonder.com",
                "phone": "111",
            },
        )

        res = await ac.get("/api/contacts/search/?query=Alice", headers=headers)

    assert res.status_code == 200
    assert len(res.json()) == 1

