"""Tumanlar va kategoriyalarni bazaga yuklaydi — qayta ishlatsa takrorlanmaydi.

Ishga tushirish:

    docker compose -f deploy/docker-compose.yml exec api python -m seeds.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory
from app.models import Category, District
from seeds.categories import CATEGORIES
from seeds.districts import TOSHKENT_DISTRICTS


async def seed_districts(session: AsyncSession) -> int:
    """Yangi tumanlarni qo'shadi, mavjudlariga tegmaydi. Qaytgan son — yangilari."""
    existing = set(await session.scalars(select(District.name_uz)))
    added = 0
    for name_uz, name_ru, latitude, longitude in TOSHKENT_DISTRICTS:
        if name_uz in existing:
            continue
        session.add(
            District(
                name_uz=name_uz,
                name_ru=name_ru,
                center=f"SRID=4326;POINT({longitude:.6f} {latitude:.6f})",
            )
        )
        added += 1
    await session.commit()
    return added


async def seed_categories(session: AsyncSession) -> int:
    """Slug bo'yicha tekshiradi — ro'yxatni to'ldirsa ham eski kategoriyalar buzilmaydi."""
    existing = set(await session.scalars(select(Category.slug)))
    added = 0
    for order, (slug, name_uz, name_ru) in enumerate(CATEGORIES, start=1):
        if slug in existing:
            continue
        session.add(Category(slug=slug, name_uz=name_uz, name_ru=name_ru, sort_order=order * 10))
        added += 1
    await session.commit()
    return added


async def main() -> None:
    async with SessionFactory() as session:
        districts = await seed_districts(session)
        categories = await seed_categories(session)
        total_districts = await session.scalar(select(func.count()).select_from(District))
        total_categories = await session.scalar(select(func.count()).select_from(Category))
    print(
        f"tumanlar: {districts} ta yangi (jami {total_districts}), "
        f"kategoriyalar: {categories} ta yangi (jami {total_categories})"
    )


if __name__ == "__main__":
    asyncio.run(main())
