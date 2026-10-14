"""Rasm yuklash API'si: pozitsiya, chegaralar, egalik va o'chirish.

R2'ga birmuncha so'rov ketmaydi — `storage` fixture'i xotiradagi saqlagichni beradi.
PostGIS bazasi kerak (TEST_DATABASE_URL bo'lmasa testlar o'tkazib yuboriladi).
"""

from __future__ import annotations

import io

import pytest
from PIL import Image
from test_listings_api import add_category, login, new_listing

from app.core.config import settings

SOURCE_SIZE = (900, 600)
CDN_BASE = "https://cdn.example.test/qoshni"


@pytest.fixture(autouse=True)
def cdn_base(monkeypatch: pytest.MonkeyPatch) -> None:
    """URLlarni aniq tekshirish uchun ommaviy manzilni test qiymatiga almashtiramiz."""
    monkeypatch.setattr(settings, "r2_public_base_url", CDN_BASE)


def jpeg_bytes(size=SOURCE_SIZE) -> bytes:
    image = Image.new("RGB", size, (30, 120, 200))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


async def upload(db_client, headers: dict[str, str], listing_id: int, **kwargs):
    return await db_client.post(
        f"/api/v1/listings/{listing_id}/images",
        files={"file": ("rasm.jpg", kwargs.get("data", jpeg_bytes()), "image/jpeg")},
        headers=headers,
    )


async def seller(db_client, db_session) -> tuple[dict[str, str], int]:
    """Sotuvchi: kiradi, joylashuvini qo'yadi va bitta e'lon yaratadi."""
    headers = await login(db_client, 910_001)
    category_id = await add_category(db_session)
    await db_client.put(
        "/api/v1/me/location",
        json={"latitude": 41.3125, "longitude": 69.2800},
        headers=headers,
    )
    listing = await new_listing(db_client, headers, category_id)
    return headers, listing["id"]


async def test_upload_creates_both_variants_and_positions(db_client, db_session, storage) -> None:
    headers, listing_id = await seller(db_client, db_session)

    first = await upload(db_client, headers, listing_id)
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["position"] == 0
    assert (body["width"], body["height"]) == SOURCE_SIZE
    assert body["url"] == f"{CDN_BASE}/{body['storage_key']}"
    assert body["thumb_url"].startswith(CDN_BASE)
    assert body["thumb_url"] != body["url"]

    second = await upload(db_client, headers, listing_id)
    assert second.json()["position"] == 1
    assert second.json()["storage_key"] != body["storage_key"]

    # Har yuklashda ikkita obyekt: asosiy rasm va @400 ko'rinishi.
    assert len(storage.objects) == 4
    for key, data in storage.objects.items():
        assert key.startswith("listings/") and data[:4] == b"RIFF"

    detail = await db_client.get(f"/api/v1/listings/{listing_id}", headers=headers)
    images = detail.json()["images"]
    assert [item["position"] for item in images] == [0, 1]
    assert images[0]["storage_key"] == body["storage_key"]


async def test_image_limit_is_six(db_client, db_session) -> None:
    headers, listing_id = await seller(db_client, db_session)

    for _ in range(6):
        assert (await upload(db_client, headers, listing_id)).status_code == 201

    rejected = await upload(db_client, headers, listing_id)
    assert rejected.status_code == 422
    assert "6" in rejected.json()["error"]["message"]


async def test_only_owner_can_upload(db_client, db_session) -> None:
    _, listing_id = await seller(db_client, db_session)
    stranger = await login(db_client, 910_002)

    response = await upload(db_client, stranger, listing_id)
    assert response.status_code == 403


async def test_delete_removes_db_row_and_both_objects(db_client, db_session, storage) -> None:
    headers, listing_id = await seller(db_client, db_session)
    body = (await upload(db_client, headers, listing_id)).json()

    deleted = await db_client.delete(
        f"/api/v1/listings/{listing_id}/images/{body['id']}", headers=headers
    )
    assert deleted.status_code == 204
    assert storage.objects == {}

    detail = await db_client.get(f"/api/v1/listings/{listing_id}", headers=headers)
    assert detail.json()["images"] == []


async def test_non_image_is_rejected_and_nothing_stored(db_client, db_session, storage) -> None:
    headers, listing_id = await seller(db_client, db_session)

    response = await upload(db_client, headers, listing_id, data=b"salom, bu rasm emas")
    assert response.status_code == 422
    assert storage.objects == {}
    assert (await db_client.get(f"/api/v1/listings/{listing_id}", headers=headers)).json()[
        "images"
    ] == []


async def test_upload_to_missing_listing_is_404(db_client) -> None:
    headers = await login(db_client, 910_003)
    assert (await upload(db_client, headers, 999_999)).status_code == 404
