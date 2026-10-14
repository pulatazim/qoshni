"""E'lon matnini tekshirish: taqiqlangan mavzu bo'lsa, e'lon umuman saqlanmaydi."""

from __future__ import annotations

import re

from app.core.errors import HTTP_UNPROCESSABLE, VALIDATION_ERROR, ApiError
from app.modules.listings.search import normalize
from app.modules.moderation.words import PHRASES, PROHIBITED

# Normalizatsiyadan keyin faqat lotin harfi va raqam qoladi — so'zlarga bo'lish oson.
_WORD_SPLIT = re.compile(r"[^0-9a-z]+")


def violation(*texts: str) -> str | None:
    """Biringi uchragan taqiqlangan mavzuning sababini qaytaradi, bo'lmasa None."""
    merged = normalize(" ".join(texts))
    if not merged:
        return None
    tokens = {word for word in _WORD_SPLIT.split(merged) if word}

    for reason, words in PROHIBITED.items():
        if tokens & set(words):
            return reason
    for reason, phrases in PHRASES.items():
        if any(phrase in merged for phrase in phrases):
            return reason
    return None


def check_listing_text(title: str, description: str) -> None:
    reason = violation(title, description)
    if reason is not None:
        raise ApiError(
            VALIDATION_ERROR,
            f"Bu mavzuda e'lon joylab bo'lmaydi: {reason}. Matnni o'zgartiring",
            HTTP_UNPROCESSABLE,
        )
