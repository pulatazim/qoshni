"""Qidiruv normalizatsiyasi: kirill va lotin yozuvini bitta ko'rinishga keltiradi.

E'lon saqlanganda `search_text` shu funksiyaning natijasi bo'ladi, so'rov ham shu
orqadan o'tadi — shunda "китоб" yozgan foydalanuvchi "kitob" e'lonini topadi.
"""

from __future__ import annotations

import re

# O'zbek kirill → lotin. Ko'p harfli kombinatsiyalar birinchi almashinadi.
CYR2LAT: dict[str, str] = {
    "щ": "shch",
    "ё": "yo",
    "ю": "yu",
    "я": "ya",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "ҳ": "h",
    "ҷ": "j",
    "ў": "o",
    "қ": "q",
    "ғ": "g",
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ъ": "",
    "ь": "",
    "ы": "i",
    "э": "e",
    "і": "i",
}

# Apostrof variantlari (oʻ, o', o’, o‘) qidiruvda farq qilmasligi uchun tashlab yuboriladi.
APOSTROPHES = "ʻʼ’‘`´‛‚׳'’"

_MULTI_CHAR_KEYS = sorted((k for k in CYR2LAT if len(k) > 1), key=len, reverse=True)
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    """Kichik harf + lotin yozuvi + qo'shimcha bo'shliqlar olib tashlanadi."""
    if not text:
        return ""
    lowered = text.lower()
    cleaned = "".join(ch for ch in lowered if ch not in APOSTROPHES)
    for cyrillic in _MULTI_CHAR_KEYS:
        cleaned = cleaned.replace(cyrillic, CYR2LAT[cyrillic])
    single = {k: v for k, v in CYR2LAT.items() if len(k) == 1}
    converted = "".join(single.get(ch, ch) for ch in cleaned)
    return _WHITESPACE.sub(" ", converted).strip()


def build_search_text(title: str, description: str) -> str:
    """Saqlanadigan `search_text` — normalizatsiyadan o'tgan sarlavha + tavsif."""
    return normalize(f"{title} {description}")
