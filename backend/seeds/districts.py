"""Toshkent tumanlari — tuman tanlash va boshlang'ich lenta radiusi uchun reference ma'lumot.

Markazlar taxminiy: ochilishdan oldin xaritada ko'z bilan tekshiriladi. Lenta filtri
foydalanuvchining GPS nuqtasidan hisoblanadi, tuman markazi faqat "tumanni qo'lda
tanladim" holati va statistika uchun kerak.
"""

# (name_uz, name_ru, latitude, longitude)
TOSHKENT_DISTRICTS: list[tuple[str, str, float, float]] = [
    ("Bektemir", "Бектемир", 41.2439, 69.3361),
    ("Bodomzor", "Бодомзор", 41.2706, 69.1958),
    ("Chilonzor", "Чиланзар", 41.2775, 69.2422),
    ("Mirzo Ulug'bek", "Мирзо Улуғбек", 41.3167, 69.3333),
    ("Mirobod", "Мирабад", 41.3069, 69.2919),
    ("Olmazor", "Алмазар", 41.3333, 69.2833),
    ("Sergeli", "Сергели", 41.2500, 69.2333),
    ("Shayxontohur", "Шайхонтохур", 41.3222, 69.2583),
    ("Uchtepa", "Учтепа", 41.2917, 69.2333),
    ("Yakkasaroy", "Яккасарой", 41.3000, 69.2833),
    ("Yashnobod", "Яшнабад", 41.2972, 69.3250),
    ("Yunusobod", "Юнусабад", 41.3500, 69.2917),
]
