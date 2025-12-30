# tests/test_roles.py
import pytest

@pytest.mark.asyncio
async def test_make_admin_forbidden_for_user(client, token_user, user_user):
    headers = {"Authorization": f"Bearer {token_user}"}
    r = await client.post(f"/api/auth/make-admin/{user_user.id}", headers=headers)
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_make_admin_allowed_for_admin(client, token_admin, user_user):
    headers = {"Authorization": f"Bearer {token_admin}"}
    r = await client.post(f"/api/auth/make-admin/{user_user.id}", headers=headers)
    assert r.status_code == 200
