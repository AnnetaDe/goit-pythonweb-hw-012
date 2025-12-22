import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from contacts_api.app.database import get_test_session, engine_test
from contacts_api.app.db_base import Base
from contacts_api.app.main import app
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def session_override() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_test_session():
        yield session


@pytest.fixture()
async def get_token(prepare_test_database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/api/auth/signup", json={
            "email": "test@example.com",
            "password": "string123"
        })
        response = await ac.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "string123"
        })
        return response.json()["access_token"]
