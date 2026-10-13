"""verify_init_data va JWT funksiyalari uchun unit testlar (bazasiz, tezkor)."""

from __future__ import annotations

import json
import time
from urllib.parse import urlencode

import jwt as pyjwt
import pytest

from app.core.config import settings
from app.core.security import (
    AuthError,
    create_access_token,
    decode_access_token,
    sign_init_data,
    verify_init_data,
)

BOT_TOKEN = "123456:TEST-bot-token-for-unit-tests"
USER = {"id": 4242, "first_name": "Aziz", "username": "aziz", "language_code": "uz"}


def make_init_data(pairs: dict[str, str], token: str = BOT_TOKEN) -> str:
    """Telegram Mini App yuboradigan initData qatorini imzolab beradi."""
    signed = {**pairs, "hash": sign_init_data(pairs, token)}
    return urlencode(signed)


def fresh_pairs(**overrides: str) -> dict[str, str]:
    pairs = {
        "auth_date": str(int(time.time())),
        "query_id": "AAH7c5YB",
        "user": json.dumps(USER),
        "start_param": "district=mirzo-ulugbek",
        "web_app_version": "1.0",
    }
    pairs.update(overrides)
    return pairs


# --- initData tekshiruvi ---


def test_valid_init_data_returns_user() -> None:
    result = verify_init_data(make_init_data(fresh_pairs()), bot_token=BOT_TOKEN)
    assert result == USER


def test_tampered_hash_is_rejected() -> None:
    init_data = make_init_data(fresh_pairs()).replace("hash=", "hash=0" + "0" * 63)
    with pytest.raises(AuthError, match="imzo"):
        verify_init_data(init_data, bot_token=BOT_TOKEN)


def test_tampered_field_after_signing_is_rejected() -> None:
    # Eski (yaroqli) imzoni saqlab, user maydonini boshqa odamga almashtiramiz.
    init_data = make_init_data(fresh_pairs())
    original_hash = dict(item.split("=", 1) for item in init_data.split("&"))["hash"]
    stolen = json.dumps({**USER, "id": 1})
    forged = urlencode({**fresh_pairs(user=stolen), "hash": original_hash})
    with pytest.raises(AuthError, match="imzo"):
        verify_init_data(forged, bot_token=BOT_TOKEN)


def test_wrong_bot_token_is_rejected() -> None:
    init_data = make_init_data(fresh_pairs())
    with pytest.raises(AuthError, match="imzo"):
        verify_init_data(init_data, bot_token="999999:other-token")


def test_missing_hash_is_rejected() -> None:
    init_data = urlencode(fresh_pairs())
    with pytest.raises(AuthError, match="hash"):
        verify_init_data(init_data, bot_token=BOT_TOKEN)


def test_expired_auth_date_is_rejected() -> None:
    old = fresh_pairs(auth_date=str(int(time.time()) - 48 * 3600))
    with pytest.raises(AuthError, match="muddati"):
        verify_init_data(make_init_data(old), bot_token=BOT_TOKEN, max_age=86400)


def test_future_and_broken_auth_date_are_rejected() -> None:
    with pytest.raises(AuthError, match="auth_date"):
        verify_init_data(make_init_data(fresh_pairs(auth_date="abc")), bot_token=BOT_TOKEN)
    pairs = fresh_pairs()
    pairs.pop("auth_date")
    with pytest.raises(AuthError, match="auth_date"):
        verify_init_data(make_init_data(pairs), bot_token=BOT_TOKEN)


def test_missing_or_broken_user_is_rejected() -> None:
    pairs = fresh_pairs()
    pairs.pop("user")
    with pytest.raises(AuthError, match="user"):
        verify_init_data(make_init_data(pairs), bot_token=BOT_TOKEN)
    with pytest.raises(AuthError, match="user"):
        verify_init_data(make_init_data(fresh_pairs(user="{shu JSON emas")), bot_token=BOT_TOKEN)
    # user JSON, lekin ichida id yo'q
    with pytest.raises(AuthError, match="id"):
        verify_init_data(
            make_init_data(fresh_pairs(user=json.dumps({"first_name": "X"}))),
            bot_token=BOT_TOKEN,
        )


def test_no_bot_token_configured_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    with pytest.raises(AuthError, match="sozlanmagan"):
        verify_init_data(make_init_data(fresh_pairs()))


# --- JWT ---


def test_jwt_roundtrip_returns_user_id() -> None:
    token = create_access_token(4242)
    assert decode_access_token(token) == 4242


def test_jwt_expiry_is_enforced() -> None:
    token = create_access_token(4242, ttl_days=-1)
    with pytest.raises(AuthError, match="JWT"):
        decode_access_token(token)


def test_jwt_signed_with_other_secret_is_rejected() -> None:
    payload = {"sub": "1", "exp": int(time.time()) + 60}
    foreign = pyjwt.encode(payload, "boshqa-kalit-" + "x" * 24, algorithm="HS256")
    with pytest.raises(AuthError, match="JWT"):
        decode_access_token(foreign)


@pytest.mark.parametrize("bad", ["", "abc", "a.b.c"])
def test_garbage_token_is_rejected(bad: str) -> None:
    with pytest.raises(AuthError, match="JWT"):
        decode_access_token(bad)
