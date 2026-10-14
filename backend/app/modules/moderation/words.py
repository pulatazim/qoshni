"""Taqiqlangan mavzular ro'yxati (boshlang'ich).

Matn `listings.search.normalize()`dan o'tadi: kichik harf, apostrofsiz, kirill→lotin.
Shuning uchun bu yerda so'zlar aynan shu ko'rinishda yoziladi ("o'q" → "oq").

Ro'yxat hali foydalanuvchi tasdig'idan o'tmagan: belgilarni kamaytirish uchun
faqat aniq so'zlar `PROHIBITED`da, shubhali iboralar `PHRASES`da turadi.
"""

from __future__ import annotations

# So'zgona moslash: e'lon matnidagi bir so'z shu ro'yxatga tushsa rad etiladi.
PROHIBITED: dict[str, tuple[str, ...]] = {
    "qurol va portlovchi moddalar": (
        "miltiq",
        "patron",
        "granata",
        "tranka",
        "elektroshok",
    ),
    "giyohvand va retsept dorilari": (
        "narkotik",
        "narkotiklar",
        "spirtli",
        "metadon",
        "subutex",
        "efedrin",
    ),
    "pornografiya": ("pornografiya", "porno", "erotik", "erotika"),
    "ekstremistik materiallar": ("ekstremizm", "daish", "ishid"),
}

# Ibora moslash: normalizatsiyadan o'tgan matnda qator ko'rinishida izlanadi.
PHRASES: dict[str, tuple[str, ...]] = {
    "firibgarlik belgilari": (
        "karta malumot",
        "karta rekvizit",
        "cvv",
        "oldindan tolov",
        "tolov skrinshot",
        "oldinga pul",
    ),
    "inson savdosi va soxta hujjat": (
        "organ sot",
        "buyrak sot",
        "soxta dipl",
        "soxta pasport",
        "spravka sot",
    ),
}
