"""So'rov va e'lon sonini cheklash.

Dizayndagi ikkita limit: bir foydalanuvchi daqiqada 60 ta so'rov yuboradi,
kuniga 20 tadan ko'p e'lon qo'ymaydi. Redis bo'lmagan muhitda (testlar, lokal)
xotira hisoblagichi ishlatiladi — kod yo'li o'zgarmaydi.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Annotated, Protocol

from fastapi import Depends

from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.errors import RATE_LIMITED, ApiError
from app.models import User

# Kunlik hisoblagich UTC kuniga to'g'ri keladi (epoch — yarim tundan boshlangan).
DAY_SECONDS = 86400
MINUTE_SECONDS = 60


class RateLimiter(Protocol):
    """`hit` — ruxsat berilsa (True, 0), bo'lmasa (False, necha soniya kutish)."""

    async def hit(
        self, scope: str, user_id: int, limit: int, window_seconds: int
    ) -> tuple[bool, int]: ...


class InMemoryRateLimiter:
    """Bitta jarayon ichida hisoblaydi. Bir nechta uvicorn xodimi bo'lsa aniqlik yo'qoladi."""

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._events: dict[str, deque[float]] = {}

    async def hit(
        self, scope: str, user_id: int, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        key = f"{scope}:{user_id}"
        now = self._clock()
        events = self._events.setdefault(key, deque())
        while events and now - events[0] >= window_seconds:
            events.popleft()

        if len(events) >= limit:
            return False, max(1, round(window_seconds - (now - events[0])))
        events.append(now)
        return True, 0


class RedisRateLimiter:
    """Hisoblagich kaliti: `rl:scope:user:bucket`.

    Bucket — oynaning tartib raqami. Shunda `INCR` va `EXPIRE` poyga qilmaydi:
    birinchi urinishda muddat qo'yiladi, oynalarning chegarasi hisobni aralashtirmaydi.
    """

    def __init__(self, redis_url: str) -> None:
        from redis import asyncio as aioredis

        self.redis = aioredis.Redis.from_url(redis_url)

    @staticmethod
    def bucket_key(scope: str, user_id: int, window_seconds: int) -> str:
        return f"rl:{scope}:{user_id}:{int(time.time() // window_seconds)}"

    async def hit(
        self, scope: str, user_id: int, limit: int, window_seconds: int
    ) -> tuple[bool, int]:
        key = self.bucket_key(scope, user_id, window_seconds)
        pipe = self.redis.pipeline(transaction=False)
        pipe.incr(key)
        count = int((await pipe.execute())[0])
        if count == 1:
            await self.redis.expire(key, window_seconds)
        if count <= limit:
            return True, 0
        ttl = await self.redis.ttl(key)
        return False, max(1, int(ttl) if ttl and ttl > 0 else window_seconds)


def build_limiter() -> RateLimiter:
    if settings.rate_limit_backend == "memory":
        return InMemoryRateLimiter()
    return RedisRateLimiter(settings.redis_url)


_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = build_limiter()
    return _limiter


LimiterDep = Annotated[RateLimiter, Depends(get_limiter)]


async def _enforce(
    limiter: RateLimiter, user: User, scope: str, limit: int, window_seconds: int
) -> None:
    allowed, retry_in = await limiter.hit(scope, user.id, limit, window_seconds)
    if allowed:
        return
    wait = f"{retry_in} soniyadan" if retry_in < 120 else f"{round(retry_in / 60)} daqiqadan"
    raise ApiError(
        RATE_LIMITED,
        f"Juda ko'p so'rov. {wait} keyin urinib ko'ring",
        429,
        retry_after=retry_in,
    )


async def minute_quota(user: CurrentUser, limiter: LimiterDep) -> None:
    """Har bir endpoint holatida qo'yiladi: daqiqalik umumiy limit."""
    await _enforce(limiter, user, "api", settings.api_requests_per_minute, MINUTE_SECONDS)


async def listing_quota(user: CurrentUser, limiter: LimiterDep) -> None:
    """E'lon yaratishga qo'yiladi: kuniga 20 tadan ortiq emas."""
    await _enforce(limiter, user, "listings", settings.listings_per_day, DAY_SECONDS)
