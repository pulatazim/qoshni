"""FastAPI dependency lari: sessiya va JWT orqali joriy foydalanuvchi."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import AUTH_INVALID, ApiError
from app.core.security import AuthError, decode_access_token
from app.core.storage import ObjectStorage, get_storage
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]
StorageDep = Annotated[ObjectStorage, Depends(get_storage)]


async def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """`Authorization: Bearer <JWT>` sarlavhasidagi foydalanuvchini qaytaradi."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(AUTH_INVALID, "Autentifikatsiya kerak", 401)
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_access_token(token)
    except AuthError as exc:
        raise ApiError(AUTH_INVALID, "Sessiyangiz muddati tugagan", 401) from exc

    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        raise ApiError(AUTH_INVALID, "Hisobingiz topilmadi yoki bloklangan", 401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
