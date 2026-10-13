"""Seeds — tumanlar va kategoriyalarni yuklash testi (PostGIS bazasi kerak)."""

from __future__ import annotations

from sqlalchemy import func, select

from app.models import Category, District
from seeds.categories import CATEGORIES
from seeds.districts import TOSHKENT_DISTRICTS
from seeds.seed import seed_categories, seed_districts


async def test_seed_loads_once_and_is_repeatable(db_session) -> None:
    assert await seed_districts(db_session) == len(TOSHKENT_DISTRICTS)
    assert await seed_categories(db_session) == len(CATEGORIES)

    # Qayta ishlatish takrorlanmaydi — deploy'da bemalol bir necha marta bosiladi.
    assert await seed_districts(db_session) == 0
    assert await seed_categories(db_session) == 0

    districts = await db_session.scalar(select(func.count()).select_from(District))
    categories = await db_session.scalar(select(func.count()).select_from(Category))
    assert districts == len(TOSHKENT_DISTRICTS)
    assert categories == len(CATEGORIES)


async def test_district_center_is_valid_geography(db_session) -> None:
    await seed_districts(db_session)
    row = await db_session.execute(
        select(func.ST_AsEWKT(District.center), func.ST_SRID(District.center)).where(
            District.name_uz == "Mirzo Ulug'bek"
        )
    )
    ewkt, srid = row.one()
    assert srid == 4326
    assert ewkt.startswith("SRID=4326;POINT(")


async def test_categories_keep_order_and_slugs(db_session) -> None:
    await seed_categories(db_session)
    slugs = list(await db_session.scalars(select(Category.slug).order_by(Category.sort_order)))
    assert slugs == [slug for slug, _, _ in CATEGORIES]
    assert len(set(slugs)) == len(slugs)
