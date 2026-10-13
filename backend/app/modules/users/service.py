"""Profil xizmati: GPS nuqtasini maxfiylik uchun yaxlitlash va joylashuvni saqlash."""

from __future__ import annotations

import math

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import HTTP_UNPROCESSABLE, NOT_FOUND, VALIDATION_ERROR, ApiError
from app.models import District, User

# Dizayn: hech kim sotuvchining aniq uyini bilmasligi uchun nuqta ~300 m katakka
# yaxlitlanadi. 1 gradus shirota ~111 320 m; uzunlik gradusi shirotaga bog'liq.
BLUR_METERS = 300.0
METERS_PER_DEGREE_LAT = 111_320.0


def blur_point(
    latitude: float, longitude: float, meters: float = BLUR_METERS
) -> tuple[float, float]:
    """Nuqtani ~meters o'lchamli katak markaziga yotqizadi (maxfiylik uchun).

    Uzunlik qadami xiralashtirilgan shirota bilan hisoblanadi — shunda bir katak ichidagi
    har qanday GPS o'qish bir xil nuqtaga tushadi.
    """
    lat_step = meters / METERS_PER_DEGREE_LAT
    blurred_lat = round(round(latitude / lat_step) * lat_step, 6)
    cos_lat = max(math.cos(math.radians(blurred_lat)), 1e-6)
    lon_step = meters / (METERS_PER_DEGREE_LAT * cos_lat)
    return blurred_lat, round(round(longitude / lon_step) * lon_step, 6)


def to_ewkt(latitude: float, longitude: float) -> str:
    """PostGIS'ning EWKT ko'rinishi — geography ustuniga shu satr yoziladi."""
    return f"SRID=4326;POINT({longitude:.6f} {latitude:.6f})"


async def update_location(
    session: AsyncSession,
    user: User,
    *,
    latitude: float | None,
    longitude: float | None,
    district_id: int | None,
) -> User:
    """GPS bo'lsa xiralashtirib saqlaydi, tuman bo'lsa tekshirib bog'laydi."""
    if latitude is None and longitude is None and district_id is None:
        raise ApiError(
            VALIDATION_ERROR,
            "Koordinata yoki tuman ko'rsatilishi kerak",
            HTTP_UNPROCESSABLE,
        )

    if (latitude is None) != (longitude is None):
        raise ApiError(
            VALIDATION_ERROR,
            "Kenglik va uzunlik birga keladi",
            HTTP_UNPROCESSABLE,
        )

    if latitude is not None and longitude is not None:
        blurred_lat, blurred_lon = blur_point(latitude, longitude)
        user.home_point = to_ewkt(blurred_lat, blurred_lon)

    if district_id is not None:
        district = await session.get(District, district_id)
        if district is None:
            raise ApiError(NOT_FOUND, "Tuman topilmadi", status.HTTP_404_NOT_FOUND)
        user.district_id = district_id

    await session.commit()
    await session.refresh(user)
    return user
