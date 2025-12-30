# tests/test_password_reset.py
import pytest
from contacts_api.app.jwt_utils import create_email_token

@pytest.mark.asyncio
async def test_password_reset_flow(client, db_session, user_user):
    # 1) request reset (не має падати, навіть якщо email існує)
    r1 = await client.post("/api/auth/request-password-reset", params={"email": user_user.email})
    assert r1.status_code == 200

    # 2) reset-password з валідним токеном
    token = create_email_token(user_user.email)
    r2 = await client.post(f"/api/auth/reset-password/{token}", json="newpass123")
    assert r2.status_code == 200
