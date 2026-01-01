# tests/conftest.py
import os
import uuid

import pytest
import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# IMPORTANT: set env BEFORE importing app/*
os.environ.setdefault("ENV", "test")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test_user:test_pass@test_db:5432/test_db"),
)
os.environ.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "secret-key"))
os.environ.setdefault("ALGORITHM", os.getenv("ALGORITHM", "HS256"))
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ---- Redis (define early) ----
REDIS_URL = os.getenv("REDIS_URL", "redis://contacts_redis:6379/0")

@pytest.fixture(scope="session")
async def redis_client():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    yield r
    await r.aclose()

@pytest.fixture(scope="function", autouse=True)
async def _clean_redis(redis_client):
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()

# ---- App imports after env ----
from contacts_api.app.main import app
from contacts_api.app.database import get_db
from contacts_api.app.models import Base, User
from contacts_api.app.jwt_utils import create_access_token
from contacts_api.app import routes_auth


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(os.environ["TEST_DATABASE_URL"], future=True)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def _create_schema(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(SessionLocal):
    async with SessionLocal() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def _override_get_db(db_session: AsyncSession):
    async def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
def _mock_email(monkeypatch):
    monkeypatch.setattr(routes_auth, "send_verification_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(routes_auth, "send_password_reset_email", lambda *args, **kwargs: None)


@pytest.fixture
async def auth_user(client: AsyncClient):
    email = f"test-{uuid.uuid4().hex}@example.com"
    await client.post("/api/auth/signup", json={"email": email, "password": "string123"})

    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            update(User)
            .where(User.email == email)
            .values(is_verified=True)
            .execution_options(synchronize_session="fetch")
        )
        await db.commit()
        db.expire_all()

    res = await client.post("/api/auth/login", json={"email": email, "password": "string123"})
    return {"email": email, "token": res.json()["access_token"]}

@pytest.fixture
async def get_token(client: AsyncClient):
    email = f"test-{uuid.uuid4().hex}@example.com"
    await client.post("/api/auth/signup", json={"email": email, "password": "string123"})

    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            update(User)
            .where(User.email == email)
            .values(is_verified=True)
            .execution_options(synchronize_session="fetch")  # <-- ключ
        )
        await db.commit()
        db.expire_all()  # <-- щоб точно не лишилось кешу

    res = await client.post("/api/auth/login", json={"email": email, "password": "string123"})
    return res.json()["access_token"]

@pytest.fixture
async def user_user(db_session: AsyncSession):
    email = f"user-{uuid.uuid4().hex}@example.com"
    u = User(email=email, hashed_password="x", is_verified=True, role="user")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def user_admin(db_session: AsyncSession):
    email = f"admin-{uuid.uuid4().hex}@example.com"
    u = User(email=email, hashed_password="x", is_verified=True, role="admin")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def token_user(user_user):
    return create_access_token(data={"sub": str(user_user.id)})


@pytest.fixture
async def token_admin(user_admin):
    return create_access_token(data={"sub": str(user_admin.id)})


@pytest.fixture(scope="function", autouse=True)
async def _clean_db(db_session: AsyncSession):
    yield
    await db_session.execute(text("TRUNCATE TABLE contacts RESTART IDENTITY CASCADE"))
    await db_session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
    await db_session.commit()
