"""Telegram initData tekshiruvi (HMAC-SHA256) va JWT ishlab chiqarish/tekshirish.

Frontend yuborgan `user.id` ga hech qachon ishonilmaydi: avval initData imzosi
bot tokeni bilan tekshiriladi, foydalanuvchi shundan keyina DB'dan olinadi.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl

import jwt

from app.core.config import settings

# Telegram hujjatidagi qat'iy so'z: HMAC kalitini shu bilan boshlaymiz.
INIT_DATA_SECRET = b"WebAppData"


class AuthError(Exception):
    """Autentifikatsiya o'tmadi. Sababi log uchun, mijozga esa yagona xato beriladi."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def build_check_string(pairs: dict[str, str]) -> str:
    """hash va bo'sh maydonlardan tashqari barcha maydonlarni saralab ulaymiz."""
    return "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))


def sign_init_data(pairs: dict[str, str], bot_token: str) -> str:
    """initData qatorini imzolaydi — testlar va lokal demo uchun kerak."""
    secret = hmac.new(INIT_DATA_SECRET, bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret, build_check_string(pairs).encode(), hashlib.sha256).hexdigest()


def verify_init_data(
    init_data: str,
    bot_token: str | None = None,
    max_age: int | None = None,
) -> dict[str, Any]:
    """initData qatorini tekshirib, ichidagi user JSON'ini qaytaradi.

    bot_token yoki max_age berilmasa, sozlamalardan olinadi.
    """
    token = bot_token if bot_token is not None else settings.bot_token()
    if not token:
        raise AuthError("telegram_bot_token sozlanmagan")

    allowed_age = settings.init_data_max_age_seconds if max_age is None else max_age

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if received_hash is None:
        raise AuthError("hash maydoni yo'q")

    secret = hmac.new(INIT_DATA_SECRET, token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, build_check_string(pairs).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise AuthError("imzo mos emas")

    auth_date = _parse_auth_date(pairs)
    if time.time() - auth_date > allowed_age:
        raise AuthError("initData muddati o'tgan")

    return _parse_user(pairs)


def _parse_auth_date(pairs: dict[str, str]) -> int:
    try:
        return int(pairs["auth_date"])
    except KeyError as exc:
        raise AuthError("auth_date maydoni yo'q") from exc
    except ValueError as exc:
        raise AuthError("auth_date son emas") from exc


def _parse_user(pairs: dict[str, str]) -> dict[str, Any]:
    try:
        user = json.loads(pairs["user"])
    except KeyError as exc:
        raise AuthError("user maydoni yo'q") from exc
    except (TypeError, json.JSONDecodeError) as exc:
        raise AuthError("user JSON emas") from exc
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise AuthError("user ichida id yo'q")
    return user


def create_access_token(user_id: int, ttl_days: int | None = None) -> str:
    """Foydalanuvchi uchun qisqa muddatli JWT (sub = foydalanuvchi ID'si)."""
    days = settings.jwt_ttl_days if ttl_days is None else ttl_days
    issued_at = int(time.time())
    payload = {"sub": str(user_id), "iat": issued_at, "exp": issued_at + days * 86400}
    return jwt.encode(payload, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """JWT'ni tekshirib foydalanuvchi ID'sini qaytaradi; yaroqsiz bo'lsa AuthError."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_signing_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise AuthError("JWT yaramaydi") from exc
