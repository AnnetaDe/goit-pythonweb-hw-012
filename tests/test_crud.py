import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from contacts_api.app import cloudinary_utils
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

@pytest.mark.asyncio
async def test_contact_not_found_404(client: AsyncClient, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}

    r1 = await client.get("/api/contacts/999999", headers=headers)
    assert r1.status_code == 404

    r2 = await client.put("/api/contacts/999999", headers=headers, json={
        "first_name": "A", "last_name": "B", "email": "a@b.com", "phone": "1"
    })
    assert r2.status_code == 404

    r3 = await client.delete("/api/contacts/999999", headers=headers)
    assert r3.status_code == 404




def test_upload_avatar_returns_secure_url(monkeypatch):
    def fake_upload(file, public_id=None, overwrite=None, folder=None, **kwargs):
        assert file == b"img"
        assert public_id.startswith("avatars/")
        assert overwrite is True
        assert folder == "avatars"
        return {"secure_url": "https://cdn.example.com/a.webp"}

    monkeypatch.setattr(cloudinary_utils.cloudinary.uploader, "upload", fake_upload)

    url = cloudinary_utils.upload_avatar(b"img", "user-1")
    assert url == "https://cdn.example.com/a.webp"


def test_upload_avatar_returns_none_when_no_url(monkeypatch):
    monkeypatch.setattr(
        cloudinary_utils.cloudinary.uploader,
        "upload",
        lambda *a, **k: {},  # no secure_url
    )

    assert cloudinary_utils.upload_avatar(b"img", "user-1") is None



@pytest.mark.asyncio
async def test_signup_conflict_409(client):
    email = "dup@example.com"
    r1 = await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    assert r1.status_code == 201

    r2 = await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_login_422_missing_fields(client):
    r = await client.post("/api/auth/login", json={"email": "a@b.com"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_verify_email_user_not_found(client, monkeypatch):
    # force token decode to some email that is NOT in DB
    monkeypatch.setattr("contacts_api.app.routes_auth.decode_email_token", lambda t: "missing@example.com")
    r = await client.get("/api/auth/verify-email/whatever")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_forbidden_if_not_verified(client):
    email = "notverified@example.com"
    await client.post("/api/auth/signup", json={"email": email, "password": "string123"})
    # login should work but /me should be 403 (not verified)
    login = await client.post("/api/auth/login", json={"email": email, "password": "string123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 403


@pytest.mark.asyncio
async def test_me_401_missing_token(client):
    r = await client.get("/api/auth/me")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_db_session_is_working(db_session):
    # hits database.py paths by doing a real query through the session
    r = await db_session.execute(text("SELECT 1"))
    assert r.scalar() == 1


@pytest.mark.asyncio
async def test_get_contacts_default_pagination_works(client, get_token):
    # hits routes.py + crud.get_contacts
    headers = {"Authorization": f"Bearer {get_token}"}
    r = await client.get("/api/contacts/", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_contact_not_found_paths(client, get_token):
    # hits crud.get_contact / update_contact / delete_contact "not found" branches
    headers = {"Authorization": f"Bearer {get_token}"}

    r1 = await client.get("/api/contacts/999999", headers=headers)
    assert r1.status_code == 404

    r2 = await client.put(
        "/api/contacts/999999",
        headers=headers,
        json={
            "first_name": "X",
            "last_name": "Y",
            "email": "x@y.com",
            "phone": "123",
            "birthday": None,
            "additional_info": None,
        },
    )
    assert r2.status_code == 404

    r3 = await client.delete("/api/contacts/999999", headers=headers)
    assert r3.status_code == 404



@pytest.mark.asyncio
async def test_create_update_delete_contact_full_flow(client, get_token):
    # hits crud.create_contact / update_contact / delete_contact success branches
    headers = {"Authorization": f"Bearer {get_token}"}

    create = await client.post(
        "/api/contacts/",
        headers=headers,
        json={
            "first_name": "A",
            "last_name": "B",
            "email": "a@b.com",
            "phone": "111",
            "birthday": None,
            "additional_info": "hi",
        },
    )
    assert create.status_code in (200, 201)
    cid = create.json()["id"]

    upd = await client.put(
        f"/api/contacts/{cid}",
        headers=headers,
        json={
            "first_name": "A2",
            "last_name": "B2",
            "email": "a2@b.com",
            "phone": "222",
            "birthday": None,
            "additional_info": "yo",
        },
    )
    assert upd.status_code == 200
    assert upd.json()["email"] == "a2@b.com"

    dele = await client.delete(f"/api/contacts/{cid}", headers=headers)
    assert dele.status_code in (200, 204)


@pytest.mark.asyncio
async def test_search_and_upcoming_birthdays(client, get_token):
    # hits crud.search_contacts + crud.get_upcoming_birthdays
    headers = {"Authorization": f"Bearer {get_token}"}

    await client.post(
        "/api/contacts/",
        headers=headers,
        json={
            "first_name": "Alice",
            "last_name": "Wonder",
            "email": "alice@wonder.com",
            "phone": "999",
            "birthday": "2000-12-31",
            "additional_info": None,
        },
    )

    s = await client.get("/api/contacts/search/?query=Alice", headers=headers)
    assert s.status_code == 200
    assert len(s.json()) >= 1

    b = await client.get("/api/contacts/birthdays", headers=headers)
    assert b.status_code == 200
    assert isinstance(b.json(), list)


@pytest.mark.asyncio
async def test_dependency_rejects_invalid_token(client):
    # hits dependencies.py "invalid token" branch (401/403 depending on your impl)
    r = await client.get("/api/contacts/", headers={"Authorization": "Bearer nope"})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_dependency_rejects_nonexistent_user_id(client):
    # hits dependencies.py "user not found" branch
    # use a token for a user id that doesn't exist (your jwt uses sub as id)
    from contacts_api.app.jwt_utils import create_access_token

    token = create_access_token(data={"sub": "999999"})
    r = await client.get("/api/contacts/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 403, 404)





