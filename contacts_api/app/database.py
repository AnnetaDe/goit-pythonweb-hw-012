from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

# Ініціалізація Base тут, щоб уникнути циклічного імпорту
Base = declarative_base()

# Основна база
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Тестова база
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
engine_test = create_async_engine(TEST_DATABASE_URL, echo=True)
async_session_test = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)

# Залежність для основної бази
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Залежність для тестів
async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        yield session
