import pytest
from httpx import AsyncClient

from contacts_api.app.auth import hash_password, verify_password


@pytest.mark.asyncio
async def test_get_contact_404(client: AsyncClient, get_token: str):
    r = await client.get(
        "/api/contacts/999999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_update_contact_404(client: AsyncClient, get_token: str):
    r = await client.put(
        "/api/contacts/999999",
        headers={"Authorization": f"Bearer {get_token}"},
        json={
            "first_name": "A",
            "last_name": "B",
            "email": "ab@example.com",
            "phone": "111",
            "birthday": None,
            "additional_info": None,
        },
    )
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_delete_contact_404(client: AsyncClient, get_token: str):
    r = await client.delete(
        "/api/contacts/999999",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert r.status_code == 404


def test_hash_and_verify_password():
    raw = "secret123"
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False