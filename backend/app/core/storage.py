"""Obyekt saqlash: Cloudflare R2 (S3 mos API) yoki xotidagi soxta saqlagich.

R2 kalitlari bo'lmagan muhitda (testlar, endi klonlangan repo) `InMemoryStorage`
tanlanadi — ish kodi bir xil qoladi, tarmoq so'rovi ketmaydi.
"""

from __future__ import annotations

import functools
import uuid
from datetime import UTC, datetime
from typing import Protocol

import anyio
from boto3 import client as boto_client
from botocore.config import Config as BotoConfig

from app.core.config import settings

# Kichik (lenta) rasmining eng uzun tomoni; kalit nomi shu raqam bilan yoziladi.
THUMB_EDGE = 400


class ObjectStorage(Protocol):
    """Faqat ikkita amal kerak: rasm yozish va o'chirish."""

    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    async def delete(self, key: str) -> None: ...


class InMemoryStorage:
    """Kalitsiz muhit uchun: hammasi jarayon xotirasida turadi."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = data

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)


class R2Storage:
    """boto3 sinxron kutubxona — event loop bloklanmasligi uchun ishchi ipga beramiz."""

    def __init__(self) -> None:
        self._client = boto_client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_key,
            region_name="auto",
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        )
        self._bucket = settings.r2_bucket

    def _put_sync(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def _delete_sync(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(functools.partial(self._put_sync, key, data, content_type))

    async def delete(self, key: str) -> None:
        await anyio.to_thread.run_sync(functools.partial(self._delete_sync, key))


def build_storage() -> ObjectStorage:
    return R2Storage() if settings.storage_configured else InMemoryStorage()


def public_url(storage_key: str) -> str:
    """Rasmning ommaviy manzili; public base sozlanmagan bo'lsa bo'sh satr."""
    base = settings.r2_public_base_url.rstrip("/")
    return f"{base}/{storage_key}" if base else ""


def thumb_url(storage_key: str) -> str:
    return public_url(thumb_key(storage_key))


def object_keys() -> tuple[str, str]:
    """R2 kalitlari juftligi: asosiy rasm va kichik ko'rinishi.

    Kichik rasm DB'da alohida ustun saqlamaydi — kaliti bitta nomdan
    `...webp` -> `...@400.webp` ko'rinishida chiqariladi.
    """
    stamp = f"{datetime.now(UTC):%Y/%m}/{uuid.uuid4().hex[:12]}"
    base = f"listings/{stamp}.webp"
    return base, thumb_key(base)


def thumb_key(storage_key: str) -> str:
    stem, _, ext = storage_key.rpartition(".")
    return f"{stem}@{THUMB_EDGE}.{ext}"


_storage: ObjectStorage | None = None


def get_storage() -> ObjectStorage:
    """FastAPI dependency — bitta saqlagich namunasi yetarli."""
    global _storage
    if _storage is None:
        _storage = build_storage()
    return _storage
