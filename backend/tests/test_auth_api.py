"""POST /auth/telegram va /me endpointlari uchun API testlar (PostGIS bazasi kerak)."""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode

import pytest
from conftest import TEST_BOT_TOKEN

from app.core.security import sign_init_data

BOT_TOKEN = TEST_BOT_TOKEN
TELEGRAM_ID = 777_001
TG_USER = {
    "id": TELEGRAM_ID,
    "first_name": "Aziz",
    "last_name": "Qodirov",
    "username": "aziz_q",
    "language_code": "uz-UZ",
}


def make_init_data(user: dict = TG_USER, auth_date: int | None = None) -> str:
    pairs = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAH7c5YB",
        "user": json.dumps(user),
    }
    return urlencode({**pairs, "hash": sign_init_data(pairs, BOT_TOKEN)})


async def login(client: pytest.FixtureRequest) -> dict:
    response = await client.post("/api/v1/auth/telegram", json={"init_data": make_init_data()})
    assert response.status_code == 200, response.text
    return response.json()


async def test_login_creates_user_and_returns_jwt(db_client) -> None:
    body = await login(db_client)

    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2
    assert body["user"]["display_name"] == "Aziz Qodirov"
    assert body["user"]["username"] == "aziz_q"
    assert body["user"]["language"] == "uz"
    assert body["user"]["trust_score"] == 50
    assert body["user"]["role"] == "user"
    assert body["user"]["has_phone"] is False


async def test_second_login_reuses_same_user(db_client) -> None:
    first = await login(db_client)
    second = await login(db_client)
    assert first["user"]["id"] == second["user"]["id"]


async def test_forged_init_data_is_rejected(db_client) -> None:
    forged = make_init_data().replace("hash=", "hash=" + "0" * 64)
    response = await db_client.post("/api/v1/auth/telegram", json={"init_data": forged})

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "auth_invalid", "message": "Kirish ma'lumoti tekshirilmadi"}
    }


async def test_expired_init_data_is_rejected(db_client) -> None:
    ancient = make_init_data(auth_date=int(time.time()) - 48 * 3600)
    response = await db_client.post("/api/v1/auth/telegram", json={"init_data": ancient})
    assert response.status_code == 401


async def test_me_requires_valid_jwt(db_client) -> None:
    anonymous = await db_client.get("/api/v1/me")
    assert anonymous.status_code == 401
    assert anonymous.json()["error"]["code"] == "auth_invalid"

    body = await login(db_client)
    unauthorized = await db_client.get("/api/v1/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert unauthorized.status_code == 401

    authorized = await db_client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert authorized.status_code == 200
    assert authorized.json()["username"] == "aziz_q"


async def test_patch_me_updates_profile(db_client) -> None:
    body = await login(db_client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    response = await db_client.patch(
        "/api/v1/me", json={"display_name": "Usta Aziz", "language": "ru"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Usta Aziz"
    assert response.json()["language"] == "ru"

    # noma'lum til qiymati sxema darajasida rad etiladi
    bad = await db_client.patch("/api/v1/me", json={"language": "de"}, headers=headers)
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "validation_error"


async def test_put_location_blurs_coordinates(db_client) -> None:
    body = await login(db_client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    response = await db_client.put(
        "/api/v1/me/location",
        json={"latitude": 41.3123456, "longitude": 69.2786543},
        headers=headers,
    )
    assert response.status_code == 200


async def test_put_location_needs_something(db_client) -> None:
    body = await login(db_client)
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    empty = await db_client.put("/api/v1/me/location", json={}, headers=headers)
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "validation_error"

    half = await db_client.put("/api/v1/me/location", json={"latitude": 41.31}, headers=headers)
    assert half.status_code == 422

    unknown_district = await db_client.put(
        "/api/v1/me/location", json={"district_id": 9999}, headers=headers
    )
    assert unknown_district.status_code == 404
    assert unknown_district.json()["error"]["code"] == "not_found"
