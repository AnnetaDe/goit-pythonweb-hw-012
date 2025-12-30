import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# IMPORTANT: for tests we must always have engine_test if TEST_DATABASE_URL exists
engine_test = None
async_session_test = None

if TEST_DATABASE_URL:
    engine_test = create_async_engine(TEST_DATABASE_URL, echo=True)
    async_session_test = async_sessionmaker(
        bind=engine_test, class_=AsyncSession, expire_on_commit=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_test is None:
        raise RuntimeError("TEST_DATABASE_URL is missing (cannot init test db)")
    async with async_session_test() as session:
        yield session
