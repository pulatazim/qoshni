"""Moderatsiya filtri: taqiqlangan mavzu, ibora va noto'g'ri signalmaslik."""

from __future__ import annotations

import pytest

from app.core.errors import ApiError
from app.modules.moderation.service import check_listing_text, violation

WEAPONS = "qurol va portlovchi moddalar"
FRAUD = "firibgarlik belgilari"


def test_prohibited_word_in_title() -> None:
    with pytest.raises(ApiError) as caught:
        check_listing_text("Miltiq sotaman", "Holati yaxshi")
    assert caught.value.code == "validation_error"
    assert "qurol" in caught.value.message


def test_prohibited_word_in_description_too() -> None:
    assert violation("Zaxira qismlar", "Ichida patron ham bor") == WEAPONS


def test_cyrillic_spelling_is_caught() -> None:
    """Kirill yozuvi normalizatsiyadan lotin bo'lib o'tadi — taqiq ham ishlaydi."""
    assert violation("Милтиқ, hujjatsiz", "") == WEAPONS
    assert violation("Эротика", "") == "pornografiya"


def test_fraud_phrase_with_apostrophe_variant_is_caught() -> None:
    """Apostrof variantlari ("to‘lov", "to'lov") bir xil ko'rinishga keladi."""
    assert violation("Ishonchli savdo", "Oldindan to'lov bo'ladi") == FRAUD
    assert violation("Buyurtma", "To‘lov skrinshotidan keyin jo'nataman") == FRAUD


def test_clean_text_passes() -> None:
    check_listing_text(
        "Eski kitob to'plami",
        "Holati yaxshi, 120 sahifa. Mirzo Ulug'bek tumani, mahalladoshga beraman",
    )


def test_substring_does_not_trigger() -> None:
    """So'zgona moslash: "Lamina" ichidagi "mina" taqiqiga tushmaydi."""
    assert violation("Lamina qo'g'irchoq", "Bolalar sovg'asi, yangi") is None
