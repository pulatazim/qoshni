"""Botni Telegram tomonida sozlash: buyruqlar ro'yxati va menyudagi Mini App tugmasi.

Ishga tushirish: `python -m app.bot.setup`
"""

from __future__ import annotations

import asyncio

from app.bot.bot import build_bot
from app.bot.ui import command_scopes, menu_button
from app.core.config import settings


async def configure() -> tuple[str, bool]:
    """Buyruqlar va menyu tugmasini yuboradi; (foydalanuvchi nomi, tugma bo'ldimi)."""
    bot = build_bot()
    try:
        me = await bot.get_me()
        for scope, commands, language in command_scopes():
            await bot.set_my_commands(commands, scope=scope, language_code=language)
        button = menu_button()
        if button is not None:
            await bot.set_chat_menu_button(menu_button=button)
        return me.username or me.first_name, button is not None
    finally:
        await bot.session.close()


def main() -> None:
    username, with_button = asyncio.run(configure())
    print(f"@{username}: /start va /app buyruqlari yuborildi")
    if with_button:
        print(f"menyu tugmasi o'rnatildi: {settings.webapp_url}")
    else:
        print("menyu tugmasi qo'yilmadi: WEBAPP_URL bo'sh")


if __name__ == "__main__":
    main()
