"""Botni uzoq so'rov (long polling) rejimida ishga tushirish: `python -m app.bot`."""

from __future__ import annotations

import asyncio
import logging

from app.bot.bot import build_bot, build_dispatcher

LOGGER = logging.getLogger("qoshni.bot")


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    bot = build_bot()
    dispatcher = build_dispatcher()
    me = await bot.get_me()
    LOGGER.info("@%s uzoq so'rov rejimida tinglayapti", me.username)
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
