"""Auth sxemalari."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.users.schemas import UserRead


class TelegramAuthRequest(BaseModel):
    """Mini App `Telegram.WebApp.initData` satrini yuboradi."""

    init_data: str = Field(min_length=16, max_length=8192)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_days: int
    user: UserRead
