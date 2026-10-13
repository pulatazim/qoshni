"""E'lon kategoriyalari — boshlang'ich ro'yxat.

DIQQAT: bu ro'yxat ishga tushirishdan oldin foydalanuvchi bilan tasdiqlanadi.
slug lotin harflari va tire bilan, o'zgartirish qiyin bo'lgani uchun ehtiyot bilan.
"""

# (slug, name_uz, name_ru)
CATEGORIES: list[tuple[str, str, str]] = [
    ("uy-asbob", "Uy-ro'zg'or asboblari", "Бытовая техника"),
    ("mebel", "Mebel va interyer", "Мебель и интерьер"),
    ("elektronika", "Elektronika", "Электроника"),
    ("kiyim", "Kiyim va poyafzal", "Одежда и обувь"),
    ("bola-uchun", "Bolalar uchun", "Детские товары"),
    ("kitob", "Kitob va o'quv materiallari", "Книги и учебные материалы"),
    ("hayvonlar", "Uy hayvonlari", "Домашние животные"),
    ("avto", "Avtomobil va ehtiyot qismlar", "Автотовары"),
    ("binnasozlik", "Ta'mir va qurilish", "Ремонт и стройматериалы"),
    ("sport", "Sport va dam olish", "Спорт и отдых"),
    ("bog-baxcha", "Bog' va hovli", "Сад и огород"),
    ("xizmat", "Xizmat ko'rsatish", "Услуги"),
    ("sovga", "Sovg'a va esdalik", "Подарки и сувениры"),
    ("boshqa", "Boshqa", "Другое"),
]
