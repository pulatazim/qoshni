"""Bot matnlari — uz/ru, foydalanuvchining Telegram tiliga qarab tanlanadi."""

from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    "uz": {
        "start": (
            "Salom{name}! Qo'shni — Toshkent qo'shnilari orasidagi e'lon bozori.\n\n"
            "Tugmani bosing va 3 km atrofdagi e'lonlarni ko'ring. "
            "O'zingiz ham keraksiz narsani bir daqiqada sotishingiz mumkin."
        ),
        "open": "E'lonlarni ko'rish",
        "help": (
            "Buyruqlar:\n"
            "/start — botni qayta ochish\n"
            "/app — Mini App'ni ochish\n\n"
            "E'lon qo'yish, qidiruv va chat Mini App ichida."
        ),
        "no_app": "Mini App hali joylashtirilmagan — tez orada ochiladi.",
        "start_desc": "Botni boshlash",
        "app_desc": "E'lonlar",
    },
    "ru": {
        "start": (
            "Привет{name}! Qo'shni — доска объявлений между соседями Ташкента.\n\n"
            "Нажмите кнопку и посмотрите объявления в радиусе 3 км. "
            "Свои ненужные вещи можно продать за минуту."
        ),
        "open": "Открыть объявления",
        "help": (
            "Команды:\n"
            "/start — перезапустить бота\n"
            "/app — открыть Mini App\n\n"
            "Размещение, поиск и чат — внутри Mini App."
        ),
        "no_app": "Mini App ещё не развёрнут — скоро откроется.",
        "start_desc": "Начать",
        "app_desc": "Объявления",
    },
}


def language_of(language_code: str | None) -> str:
    """Telegram til kodi: 'ru...' bo'lsa ruscha, aks holda o'zbekcha."""
    return "ru" if language_code and language_code.startswith("ru") else "uz"


def text(key: str, language: str, **kwargs: str) -> str:
    return TEXTS[language].get(key, TEXTS["uz"][key]).format(**kwargs)
