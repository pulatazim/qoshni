"""Katalog xizmatlari: faol kategoriyalar va Toshkent tumanlari."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, District
from app.modules.catalog.schemas import CategoryRead, DistrictRead
from app.modules.users.service import parse_ewkt


async def list_categories(session: AsyncSession) -> list[CategoryRead]:
    rows = await session.scalars(
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.id)
    )
    return [CategoryRead.model_validate(row) for row in rows]


async def list_districts(session: AsyncSession) -> list[DistrictRead]:
    # `center` — geography ustuni va ST_Y/ST_X geography'ni bilmaydi: EWKT satrini
    # olib, `parse_ewkt` bilan ochamiz (profil joylashuvidagi usul bilan bir xil).
    rows = await session.execute(
        select(
            District.id,
            District.name_uz,
            District.name_ru,
            func.ST_AsEWKT(District.center),
        ).order_by(District.name_uz)
    )
    result: list[DistrictRead] = []
    for row in rows:
        coordinates = parse_ewkt(row[3])
        if coordinates is None:
            continue
        latitude, longitude = coordinates
        result.append(
            DistrictRead(
                id=row[0],
                name_uz=row[1],
                name_ru=row[2],
                latitude=latitude,
                longitude=longitude,
            )
        )
    return result
