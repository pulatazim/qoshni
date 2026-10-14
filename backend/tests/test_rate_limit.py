"""Cheklovlar: daqiqalik so'rov va kunlik e'lon soni.

API qismi PostGIS bazasini, Redis qismi esa `TEST_REDIS_URL` bazasini talab qiladi —
sozlanmagan bo'lsa ular o'tkazib yuboriladi.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from test_listings_api import add_category, init_data, login, new_listing

from app.core.config import settings
from app.core.rate_limit import InMemoryRateLimiter, RedisRateLimiter

TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "")


async def test_in_memory_blocks_after_limit_and_isolates_users() -> None:
    limiter = InMemoryRateLimiter()

    for _ in range(3):
        assert await limiter.hit("api", 1, 3, 60) == (True, 0)

    allowed, retry_in = await limiter.hit("api", 1, 3, 60)
    assert allowed is False
    assert 1 <= retry_in <= 60
    # Boshqa foydalanuvchi va boshqa maqsad (scope) ta'sirlanmaydi.
    assert await limiter.hit("api", 2, 3, 60) == (True, 0)
    assert await limiter.hit("listings", 1, 3, 60) == (True, 0)


async def test_in_memory_window_slides() -> None:
    clock = [1_000.0]
    limiter = InMemoryRateLimiter(clock=lambda: clock[0])

    assert await limiter.hit("api", 7, 2, 60) == (True, 0)
    assert await limiter.hit("api", 7, 2, 60) == (True, 0)
    assert (await limiter.hit("api", 7, 2, 60))[0] is False

    clock[0] += 59  # oyning yopilishiga 1 soniya — birinchi urinish hali hisobda
    assert (await limiter.hit("api", 7, 2, 60))[0] is False

    clock[0] += 2  # endi hammasi eskirgan
    assert await limiter.hit("api", 7, 2, 60) == (True, 0)


@pytest.mark.skipif(not TEST_REDIS_URL, reason="TEST_REDIS_URL sozlanmagan")
async def test_redis_limiter_counts_and_sets_ttl() -> None:
    limiter = RedisRateLimiter(TEST_REDIS_URL)
    user_id = uuid4().int % 1_000_000  # har ishga tushishda yangi hisob
    window = 60

    for _ in range(2):
        assert await limiter.hit("apitest", user_id, 2, window) == (True, 0)

    allowed, retry_in = await limiter.hit("apitest", user_id, 2, window)
    assert allowed is False
    assert 1 <= retry_in <= window

    # Kalit o'ynab bo'lgach o'z-o'zidan yo'qoladi — Redis shishib ketmaydi.
    key = limiter.bucket_key("apitest", user_id, window)
    ttl = await limiter.redis.ttl(key)
    assert 0 < ttl <= window
    # Boshqa foydalanuvchi shu oynada ta'sirlanmaydi.
    assert await limiter.hit("apitest", user_id + 1, 2, window) == (True, 0)
    await limiter.redis.delete(limiter.bucket_key("apitest", user_id + 1, window))


async def test_minute_quota_blocks_fourth_request(db_client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_requests_per_minute", 3)
    headers = await login(db_client, 920_001)
    await add_category(db_session)

    for _ in range(3):
        ok = await db_client.get("/api/v1/listings/mine", headers=headers)
        assert ok.status_code == 200, ok.text

    blocked = await db_client.get("/api/v1/listings/mine", headers=headers)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert int(blocked.headers["retry-after"]) >= 1

    # Boshqa foydalanuvchi shu daqiqada o'z limitiga ega.
    other = await login(db_client, 920_002)
    assert (await db_client.get("/api/v1/listings/mine", headers=other)).status_code == 200


async def test_daily_listing_quota(db_client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(settings, "listings_per_day", 2)
    monkeypatch.setattr(settings, "api_requests_per_minute", 100)
    headers = await login(db_client, 920_003)
    category_id = await add_category(db_session)

    await new_listing(db_client, headers, category_id, title="Birinchi stol")
    await new_listing(db_client, headers, category_id, title="Ikkinchi stol")

    third = await db_client.post(
        "/api/v1/listings",
        json={
            "title": "Uchinchi stol",
            "description": "Kunlik limitdan oshdi",
            "price": 50_000,
            "category_id": category_id,
        },
        headers=headers,
    )
    assert third.status_code == 429, third.text
    assert third.json()["error"]["code"] == "rate_limited"
    # Kunlik oyna — kutish bir kundan oshmaydi.
    assert 0 < int(third.headers["retry-after"]) <= 86400

    # Yangi foydalanuvchining kunlik hisobi alohida.
    fresh = await login(db_client, 920_004)
    await new_listing(db_client, fresh, category_id, title="Uning stoli")


async def test_rate_limited_error_shape_matches_envelope(db_client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_requests_per_minute", 1)
    headers = await login(db_client, 920_005)
    assert (await db_client.get("/api/v1/listings/mine", headers=headers)).status_code == 200

    blocked = await db_client.get("/api/v1/listings/mine", headers=headers)
    assert set(blocked.json()) == {"error"}
    assert set(blocked.json()["error"]) == {"code", "message"}
    assert isinstance(blocked.json()["error"]["message"], str)


async def test_auth_is_not_limited_but_listings_are(db_client, monkeypatch) -> None:
    """Kirish so'rovi cheklovga kirmaydi — aks holda foydalanuvchi ildagida qoladi."""
    monkeypatch.setattr(settings, "api_requests_per_minute", 1)
    headers = await login(db_client, 920_006)
    assert (await db_client.get("/api/v1/listings/mine", headers=headers)).status_code == 200

    for _ in range(3):
        again = await db_client.post(
            "/api/v1/auth/telegram", json={"init_data": init_data(920_006)}
        )
        assert again.status_code == 200, again.text
    assert (await db_client.get("/api/v1/listings/mine", headers=headers)).status_code == 429
