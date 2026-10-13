"""Telegram user JSON'idan foydalanuvchini yaratadi yoki mavjudini yangilaydi."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AUTH_BANNED, ApiError
from app.models import User

SUPPORTED_LANGUAGES = {"uz", "ru"}
MAX_DISPLAY_NAME = 64


def display_name_from(tg_user: dict[str, Any]) -> str:
    """Ism va familiyani birlashtiradi; hech bo'lmasa username yoki umumiy atama qoladi."""
    parts = [str(tg_user.get(key) or "").strip() for key in ("first_name", "last_name")]
    name = " ".join(part for part in parts if part)
    return (name or str(tg_user.get("username") or "") or "Qo'shni")[:MAX_DISPLAY_NAME]


def language_from(tg_user: dict[str, Any]) -> str:
    """Telegram til kodini uz|ru ga keltiradi (ru_RU -> ru)."""
    code = (tg_user.get("language_code") or "uz")[:2].lower()
    return code if code in SUPPORTED_LANGUAGES else "uz"


async def upsert_from_telegram(session: AsyncSession, tg_user: dict[str, Any]) -> User:
    """initData'dan o'qilgan user bo'yicha profilni yaratadi/yangilaydi va qaytaradi."""
    telegram_id = int(tg_user["id"])
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=tg_user.get("username"),
            display_name=display_name_from(tg_user),
            language=language_from(tg_user),
            last_seen_at=datetime.now(UTC),
        )
        session.add(user)
    else:
        if user.status != "active":
            raise ApiError(AUTH_BANNED, "Hisobingiz bloklangan", status.HTTP_403_FORBIDDEN)
        user.username = tg_user.get("username") or user.username
        user.display_name = display_name_from(tg_user)
        user.language = language_from(tg_user)
        user.last_seen_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(user)
    return user
