import os
from collections.abc import AsyncIterator

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models
from app.core.config import settings
from app.core.db import Base, get_session
from app.main import app

# Testlarda ishlatiladigan soxta bot tokeni: initData imzosi shu bilan yasalanadi.
TEST_BOT_TOKEN = "123456:test-bot-token"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")


@pytest.fixture
def app_bot_token(monkeypatch: pytest.MonkeyPatch) -> str:
    """Iloha sozlamasiga test bot tokenini qo'yadi (haqiqiy token kerak emas)."""
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr(TEST_BOT_TOKEN))
    return TEST_BOT_TOKEN


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """Baza kerak bo'lmagan so'rovlar uchun (health, sxemalar)."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as session:
        yield session


@pytest.fixture
async def db_client(app_bot_token: str) -> AsyncIterator[httpx.AsyncClient]:
    """TEST_DATABASE_URL'dagi bazaga ulanadi; CI'da bu PostGIS service'i.

    Har testdan oldin jadvallar qayta yaratiladi, shuning uchun ma'lumot aralashmaydi.
    """
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL sozlanmagan — PostGIS bazasi kerak")

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as session:
            yield session
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
