"""E'lon API testlari: yaratish, geo-lenta, qidiruv, sahifalash, holat, o'chirish.

PostGIS bazasi kerak (TEST_DATABASE_URL bo'lmasa testlar o'tkazib yuboriladi).
"""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode

from conftest import TEST_BOT_TOKEN

from app.core.security import sign_init_data
from app.models import Category

# Mirzo Ulug'bek tumani atrofi — lentaning markazi sifatida ishlatiladi.
LAT = 41.3125
LON = 69.2800
# ~6,7 km uzoqroq nuqta (radius testlari uchun).
FAR_LAT = 41.3725


def init_data(telegram_id: int) -> str:
    user = {"id": telegram_id, "first_name": "Qoshni", "username": f"qo{telegram_id}"}
    pairs = {
        "auth_date": str(int(time.time())),
        "query_id": "AAH7c5YB",
        "user": json.dumps(user),
    }
    return urlencode({**pairs, "hash": sign_init_data(pairs, TEST_BOT_TOKEN)})


async def login(client, telegram_id: int) -> dict[str, str]:
    """Telegram orqali kirib, Authorization sarlavhasini qaytaradi."""
    response = await client.post(
        "/api/v1/auth/telegram", json={"init_data": init_data(telegram_id)}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def me_id(client, headers: dict[str, str]) -> int:
    response = await client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["id"]


async def add_category(session, slug: str = "kitob") -> int:
    category = Category(slug=slug, name_uz="Kitoblar", name_ru="Книги", sort_order=1)
    session.add(category)
    await session.commit()
    return category.id


async def new_listing(client, headers: dict[str, str], category_id: int, **overrides) -> dict:
    payload = {
        "title": "Eski kitob to'plami",
        "description": "Holati yaxshi, 120 sahifa",
        "price": 50_000,
        "category_id": category_id,
        "latitude": LAT,
        "longitude": LON,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/listings", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def feed(client, headers: dict[str, str], **params) -> dict:
    query = {"latitude": LAT, "longitude": LON, **params}
    response = await client.get("/api/v1/listings", params=query, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def test_create_listing_and_see_it_in_feed(db_client, db_session) -> None:
    headers = await login(db_client, 900_001)
    category_id = await add_category(db_session)

    created = await new_listing(db_client, headers, category_id)
    assert created["status"] == "active"
    assert created["price"] == 50_000
    assert created["view_count"] == 0
    assert created["images"] == []

    page = await feed(db_client, headers, radius=1000)
    matched = [item for item in page["items"] if item["id"] == created["id"]]
    assert len(matched) == 1
    # Joylashuv xiralashtirilgani uchun masofa 0 ga teng emas, lekin ~300 m dan ortmaydi.
    assert matched[0]["distance_m"] is not None
    assert matched[0]["distance_m"] <= 450


async def test_listing_without_gps_uses_profile_location(db_client, db_session) -> None:
    headers = await login(db_client, 900_002)
    category_id = await add_category(db_session)

    placed = await db_client.put(
        "/api/v1/me/location", json={"latitude": LAT, "longitude": LON}, headers=headers
    )
    assert placed.status_code == 200, placed.text

    payload = {
        "title": "GPS siz e'lon",
        "description": "Profaillagi joy ishlatiladi",
        "category_id": category_id,
    }
    created = await db_client.post("/api/v1/listings", json=payload, headers=headers)
    assert created.status_code == 201, created.text

    # Na so'rovda, na e'londa koordinata bor — profil joylashuvi yetarli.
    page = await db_client.get("/api/v1/listings", headers=headers)
    assert page.status_code == 200, page.text
    assert [item["id"] for item in page.json()["items"]] == [created.json()["id"]]


async def test_feed_needs_location(db_client) -> None:
    headers = await login(db_client, 900_003)
    response = await db_client.get("/api/v1/listings", headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_radius_filters_far_listing_out(db_client, db_session) -> None:
    headers = await login(db_client, 900_004)
    category_id = await add_category(db_session)
    created = await new_listing(db_client, headers, category_id, latitude=FAR_LAT)

    near = await feed(db_client, headers, radius=3000)
    assert created["id"] not in [item["id"] for item in near["items"]]

    wide = await feed(db_client, headers, radius=9000)
    assert created["id"] in [item["id"] for item in wide["items"]]


async def test_cursor_pages_have_no_duplicates(db_client, db_session) -> None:
    headers = await login(db_client, 900_005)
    category_id = await add_category(db_session)
    created_ids = {
        (await new_listing(db_client, headers, category_id, title=f"Kitob {i}"))["id"]
        for i in range(5)
    }

    seen: list[int] = []
    cursor = None
    for _ in range(10):
        params = {"radius": 3000, "limit": 2}
        if cursor:
            params["cursor"] = cursor
        page = await feed(db_client, headers, **params)
        seen.extend(item["id"] for item in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert cursor is None, "Sahifalar tugamadi"
    assert sorted(seen) == sorted(created_ids)
    assert len(seen) == len(set(seen)), "Bitta e'lon ikki marta chiqdi"


async def test_cyrillic_query_finds_latin_listing(db_client, db_session) -> None:
    headers = await login(db_client, 900_006)
    category_id = await add_category(db_session)
    created = await new_listing(
        db_client, headers, category_id, title="Chiqma kitob", description="Eski, lekin toza"
    )
    await new_listing(db_client, headers, category_id, title="Stul", description="Yog'och")

    found = await feed(db_client, headers, q="китоб")
    assert [item["id"] for item in found["items"]] == [created["id"]]

    missing = await feed(db_client, headers, q="mebel")
    assert missing["items"] == []


async def test_filters_and_cheap_sort(db_client, db_session) -> None:
    headers = await login(db_client, 900_007)
    category_id = await add_category(db_session)
    other = await add_category(db_session, slug="mebel")

    cheap = await new_listing(db_client, headers, category_id, title="Arzon kitob", price=1_000)
    mid = await new_listing(db_client, headers, category_id, title="O'rtacha kitob", price=2_000)
    await new_listing(db_client, headers, other, title="Qimmat mebel", price=3_000)

    by_category = await feed(db_client, headers, category=category_id)
    assert sorted(item["id"] for item in by_category["items"]) == sorted([cheap["id"], mid["id"]])

    by_price = await feed(db_client, headers, price_max=1_500)
    assert [item["id"] for item in by_price["items"]] == [cheap["id"]]

    ordered = await feed(db_client, headers, sort="cheap")
    assert [item["price"] for item in ordered["items"]] == [1_000, 2_000, 3_000]


async def test_status_change_hides_sold_listing(db_client, db_session) -> None:
    headers = await login(db_client, 900_008)
    category_id = await add_category(db_session)
    created = await new_listing(db_client, headers, category_id)

    updated = await db_client.post(
        f"/api/v1/listings/{created['id']}/status", json={"status": "sold"}, headers=headers
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "sold"

    assert created["id"] not in [item["id"] for item in (await feed(db_client, headers))["items"]]

    mine = await db_client.get("/api/v1/listings/mine", headers=headers)
    assert [item["status"] for item in mine.json()["items"]] == ["sold"]

    bad = await db_client.post(
        f"/api/v1/listings/{created['id']}/status", json={"status": "deleted"}, headers=headers
    )
    assert bad.status_code == 422


async def test_other_users_listing_is_protected(db_client, db_session) -> None:
    owner = await login(db_client, 900_009)
    stranger = await login(db_client, 900_010)
    category_id = await add_category(db_session)
    created = await new_listing(db_client, owner, category_id)

    change = await db_client.post(
        f"/api/v1/listings/{created['id']}/status", json={"status": "sold"}, headers=stranger
    )
    assert change.status_code == 403
    assert change.json()["error"]["code"] == "forbidden"

    remove = await db_client.delete(f"/api/v1/listings/{created['id']}", headers=stranger)
    assert remove.status_code == 403

    # O'qishga va ko'rishlar hisobiga ruxsat bor.
    read = await db_client.get(f"/api/v1/listings/{created['id']}", headers=stranger)
    assert read.status_code == 200
    assert read.json()["seller_id"] == await me_id(db_client, owner)
    assert read.json()["view_count"] == 1


async def test_soft_delete_removes_everywhere(db_client, db_session) -> None:
    headers = await login(db_client, 900_011)
    category_id = await add_category(db_session)
    created = await new_listing(db_client, headers, category_id)

    removed = await db_client.delete(f"/api/v1/listings/{created['id']}", headers=headers)
    assert removed.status_code == 204

    assert (
        await db_client.get(f"/api/v1/listings/{created['id']}", headers=headers)
    ).status_code == 404
    assert created["id"] not in [item["id"] for item in (await feed(db_client, headers))["items"]]
    assert (await db_client.get("/api/v1/listings/mine", headers=headers)).json()["items"] == []


async def test_view_count_increases_on_detail(db_client, db_session) -> None:
    headers = await login(db_client, 900_012)
    category_id = await add_category(db_session)
    created = await new_listing(db_client, headers, category_id)

    first = await db_client.get(f"/api/v1/listings/{created['id']}", headers=headers)
    second = await db_client.get(f"/api/v1/listings/{created['id']}", headers=headers)
    assert first.json()["view_count"] == 1
    assert second.json()["view_count"] == 2

    page = await feed(db_client, headers)
    assert [item["view_count"] for item in page["items"]] == [2]


async def test_unknown_category_is_rejected(db_client) -> None:
    headers = await login(db_client, 900_013)
    payload = {"title": "Noma'lum kategoriya", "description": "", "category_id": 999_999}
    response = await db_client.post("/api/v1/listings", json=payload, headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_prohibited_topic_never_reaches_the_database(db_client, db_session) -> None:
    """Taqiqlangan mavzu saqlanmaydi — e'lon bazaga tushmaydi ham."""
    headers = await login(db_client, 900_014)
    category_id = await add_category(db_session)

    rejected = await db_client.post(
        "/api/v1/listings",
        json={"title": "Miltiq sotaman", "description": "Hujjati bor", "category_id": category_id},
        headers=headers,
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "validation_error"
    assert "qurol" in rejected.json()["error"]["message"]

    mine = await db_client.get("/api/v1/listings/mine", headers=headers)
    assert mine.json()["items"] == []


async def test_fraud_phrase_is_rejected(db_client, db_session) -> None:
    headers = await login(db_client, 900_015)
    category_id = await add_category(db_session)

    response = await db_client.post(
        "/api/v1/listings",
        json={
            "title": "Ishonchli arzon telefon",
            "description": "Karta rekvizit yozib yuboring",
            "category_id": category_id,
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert "firibgarlik" in response.json()["error"]["message"]
