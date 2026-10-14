"""E'lonlarning ish biznigi: yaratish, geo-lenta, qidiruv, holat o'zgarishi."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

from fastapi import status
from sqlalchemy import Select, func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import (
    FORBIDDEN,
    HTTP_UNPROCESSABLE,
    NOT_FOUND,
    VALIDATION_ERROR,
    ApiError,
)
from app.models import Category, Listing, User
from app.modules.listings.search import build_search_text, normalize
from app.modules.users.service import blur_point, home_coordinates, to_ewkt

# Ochilish: 3 km radiusdan boshlanadi, lekin 20 km gacha ruxsat beramiz.
DEFAULT_RADIUS_M = 3000
MAX_RADIUS_M = 20000
MAX_PAGE_SIZE = 50
# Ommaga ko'rinadigan moderatsiya holatlari (pending/rejected lentaga chiqmaydi).
PUBLIC_MODERATION = ("auto_ok", "approved")


def _encode_cursor(values: list[Any]) -> str:
    raw = "|".join(str(v) for v in values)
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str | None) -> list[str] | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiError(VALIDATION_ERROR, "Sahifa kaliti buzilgan", HTTP_UNPROCESSABLE) from exc
    return raw.split("|")


def _me_geography(session: AsyncSession, latitude: float, longitude: float):
    return func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)


def _like_pattern(token: str) -> str:
    """LIKE naqshiga aylantiramiz: foydalanuvchi yozgan % va _ belgilari zararsizlantiriladi."""
    escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def create_listing(
    session: AsyncSession,
    user: User,
    *,
    title: str,
    description: str,
    price: int,
    price_type: str,
    condition: str,
    category_id: int,
    latitude: float | None,
    longitude: float | None,
) -> Listing:
    category = await session.get(Category, category_id)
    if category is None or not category.is_active:
        raise ApiError(NOT_FOUND, "Kategoriya topilmadi", status.HTTP_404_NOT_FOUND)

    if latitude is None or longitude is None:
        home = await home_coordinates(session, user)
        if home is None:
            raise ApiError(
                VALIDATION_ERROR,
                "Joylashuvni yuboring yoki profilga GPS qo'shing",
                HTTP_UNPROCESSABLE,
            )
        latitude, longitude = home

    blurred_lat, blurred_lon = blur_point(latitude, longitude)
    listing = Listing(
        seller_id=user.id,
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        price_type=price_type,
        condition=condition,
        location=to_ewkt(blurred_lat, blurred_lon),
        district_id=user.district_id,
        search_text=build_search_text(title, description),
    )
    session.add(listing)
    await session.commit()
    return await get_listing(session, listing.id)


async def get_listing(session: AsyncSession, listing_id: int) -> Listing:
    # session.get() identifikator xotiradan obyektni qaytarsa, rasmlarni yuklamaydi
    # va async kontekstda kechiktirilgan yuklash xato beradi — shuning uchun so'rov bilan.
    listing = await session.scalar(
        select(Listing).options(selectinload(Listing.images)).where(Listing.id == listing_id)
    )
    if listing is None or listing.deleted_at is not None:
        raise ApiError(NOT_FOUND, "E'lon topilmadi", status.HTTP_404_NOT_FOUND)
    return listing


async def get_owned_listing(session: AsyncSession, user: User, listing_id: int) -> Listing:
    """E'lon mavjudligi va unga egalik tekshiruvi (begona e'lon — 403)."""
    listing = await get_listing(session, listing_id)
    if listing.seller_id != user.id:
        raise ApiError(FORBIDDEN, "Bu e'lon sizniki emas", status.HTTP_403_FORBIDDEN)
    return listing


async def feed(
    session: AsyncSession,
    *,
    latitude: float | None,
    longitude: float | None,
    radius_m: int = DEFAULT_RADIUS_M,
    category_id: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    condition: str | None = None,
    price_type: str | None = None,
    query: str | None = None,
    sort: str = "new",
    cursor: str | None = None,
    limit: int = 20,
    seller_id: int | None = None,
) -> tuple[list[Listing], str | None]:
    """Radius ichidagi faol e'lonlar; cursor bilan sahifalash (offset ishlatilmaydi)."""
    if latitude is None or longitude is None:
        raise ApiError(
            VALIDATION_ERROR,
            "Lenta uchun joylashuv kerak",
            HTTP_UNPROCESSABLE,
        )
    if radius_m < 1 or radius_m > MAX_RADIUS_M:
        raise ApiError(
            VALIDATION_ERROR, f"Radius 1..{MAX_RADIUS_M} m oralig'ida", HTTP_UNPROCESSABLE
        )

    limit = max(1, min(limit, MAX_PAGE_SIZE))
    me = _me_geography(session, latitude, longitude)
    distance = func.ST_Distance(Listing.location, me).label("distance_m")

    statement: Select = (
        select(Listing, distance)
        .where(Listing.deleted_at.is_(None))
        .where(Listing.status == "active")
        .where(Listing.moderation.in_(PUBLIC_MODERATION))
        .where(func.ST_DWithin(Listing.location, me, radius_m))
    )

    if category_id is not None:
        statement = statement.where(Listing.category_id == category_id)
    if seller_id is not None:
        statement = statement.where(Listing.seller_id == seller_id)
    if price_min is not None:
        statement = statement.where(Listing.price >= price_min)
    if price_max is not None:
        statement = statement.where(Listing.price <= price_max)
    if condition is not None:
        statement = statement.where(Listing.condition == condition)
    if price_type is not None:
        statement = statement.where(Listing.price_type == price_type)
    if query:
        # Nima qidirilishini `search_text` (lotin, kichik harf) bilan solishtiramiz.
        # ILIKE tanlanadi, chunki trigramning `%` operatori qisqa so'zni uzun matnda
        # topa olmaydi (o'xshashlik uzun matn hisobiga bo'linadi). GIN trigram indeksi
        # ILIKE'ni ham tezlashtiradi — 3+ belgili token uchun indeksdan foydalaniladi.
        normalized = normalize(query)
        tokens = [token for token in normalized.split() if len(token) >= 2]
        for token in tokens:
            pattern = _like_pattern(token)
            statement = statement.where(Listing.search_text.ilike(pattern, escape="\\"))

    decoded = _decode_cursor(cursor)
    if sort in ("cheap", "expensive"):
        # Keyset sahifalash: tartib ustunlari bilan solishtiruv bir xil yo'nalishda bo'ladi.
        ascending = sort == "cheap"
        step = tuple_(Listing.price, Listing.id)
        if decoded:
            bounds = (int(decoded[0]), int(decoded[1]))
            statement = statement.where(step > bounds if ascending else step < bounds)
        order = (
            (Listing.price.asc(), Listing.id.asc())
            if ascending
            else (
                Listing.price.desc(),
                Listing.id.desc(),
            )
        )
        statement = statement.order_by(*order)
    else:
        if decoded:
            bumped = datetime.fromtimestamp(int(decoded[0]) / 1_000_000, tz=UTC)
            statement = statement.where(
                tuple_(Listing.bumped_at, Listing.id) < (bumped, int(decoded[1]))
            )
        statement = statement.order_by(Listing.bumped_at.desc(), Listing.id.desc())

    rows = (await session.execute(statement.limit(limit + 1))).all()
    has_more = len(rows) > limit
    page = rows[:limit]

    listings: list[Listing] = []
    for listing, distance_m in page:
        listing.distance_m = distance_m  # type: ignore[attr-defined]
        listings.append(listing)

    next_cursor = None
    if has_more and page:
        last = page[-1][0]
        if sort in ("cheap", "expensive"):
            next_cursor = _encode_cursor([last.price, last.id])
        else:
            stamp = int(last.bumped_at.replace(tzinfo=UTC).timestamp() * 1_000_000)
            next_cursor = _encode_cursor([stamp, last.id])
    return listings, next_cursor


async def register_view(session: AsyncSession, listing: Listing) -> None:
    """Ko'rishlar sonini atomik ravishda oshiradi va obyektdagi qiymatni yangilaydi."""
    await session.execute(
        update(Listing).where(Listing.id == listing.id).values(view_count=Listing.view_count + 1)
    )
    await session.commit()
    await session.refresh(listing, attribute_names=["view_count"])


async def list_mine(
    session: AsyncSession,
    user: User,
    *,
    state: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Listing], str | None]:
    """O'z e'lonlarim: joylashuv talab qilinmaydi, ID bo'yicha sahifalanadi."""
    if state not in (None, "active", "reserved", "sold", "hidden", "removed"):
        raise ApiError(VALIDATION_ERROR, "Holat noto'g'ri", HTTP_UNPROCESSABLE)

    limit = max(1, min(limit, MAX_PAGE_SIZE))
    statement = (
        select(Listing)
        .where(Listing.seller_id == user.id)
        .where(Listing.deleted_at.is_(None))
        .order_by(Listing.id.desc())
    )
    if state:
        statement = statement.where(Listing.status == state)

    decoded = _decode_cursor(cursor)
    if decoded:
        statement = statement.where(Listing.id < int(decoded[0]))

    rows = list(await session.scalars(statement.limit(limit + 1)))
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = _encode_cursor([page[-1].id]) if has_more and page else None
    return page, next_cursor


async def change_status(
    session: AsyncSession, user: User, listing: Listing, new_status: str
) -> Listing:
    if listing.seller_id != user.id:
        raise ApiError(
            FORBIDDEN, "Faqat o'z e'loningizni o'zgartira olasiz", status.HTTP_403_FORBIDDEN
        )
    listing.status = new_status
    await session.commit()
    # Qayta o'qib olsak rasmlar ham birga keladi (API javobi uchun kerak).
    return await get_listing(session, listing.id)


async def soft_delete(session: AsyncSession, user: User, listing: Listing) -> Listing:
    if listing.seller_id != user.id:
        raise ApiError(
            FORBIDDEN, "Faqat o'z e'loningizni o'chira olasiz", status.HTTP_403_FORBIDDEN
        )
    listing.deleted_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(listing)
    return listing
