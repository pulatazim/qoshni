"""POST /auth/telegram — Mini App kirishi."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.deps import SessionDep
from app.core.errors import AUTH_INVALID, ApiError
from app.core.security import AuthError, create_access_token, verify_init_data
from app.modules.auth import schemas
from app.modules.auth.service import upsert_from_telegram
from app.modules.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=schemas.TokenResponse, status_code=status.HTTP_200_OK)
async def telegram_auth(
    payload: schemas.TelegramAuthRequest, session: SessionDep
) -> schemas.TokenResponse:
    """initData imzosini tekshiradi, profilni yaratadi/yangilaydi va JWT beradi.

    Diqqat: foydalanuvchi ID'si frontend yuborgan JSON'dan olinadi, `user.id`
    maydoniga esa yo'l qo'yilmaydi — imzo tekshirilmagan bo'lsa so'rov rad etiladi.
    """
    try:
        tg_user = verify_init_data(payload.init_data)
    except AuthError as exc:
        raise ApiError(
            AUTH_INVALID, "Kirish ma'lumoti tekshirilmadi", status.HTTP_401_UNAUTHORIZED
        ) from exc

    user = await upsert_from_telegram(session, tg_user)
    return schemas.TokenResponse(
        access_token=create_access_token(user.id),
        expires_in_days=settings.jwt_ttl_days,
        user=UserRead.model_validate(user),
    )
