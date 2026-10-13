"""Foydalanuvchi profilining API sxemalari."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    """Profil — o'zi uchun to'liq; telefon faqat mavjudligi bilan ko'rsatiladi."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    username: str | None
    language: str
    district_id: int | None
    trust_score: int
    role: str
    has_phone: bool = False


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=64)
    language: Literal["uz", "ru"] | None = None


class LocationUpdate(BaseModel):
    """GPS nuqtasi yoki tuman tanlovi. Ikkalasi ham bo'sh bo'lishi mumkin emas."""

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    district_id: int | None = None
