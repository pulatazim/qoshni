"""Bot va dispatcher obyektlarini yig'ish."""

from __future__ import annotations

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings


class BotNotConfigured(RuntimeError):
    """TELEGRAM_BOT_TOKEN sozlanmagan — bot ishga tushmaydi."""


def build_bot() -> Bot:
    token = settings.bot_token()
    if not token:
        raise BotNotConfigured("TELEGRAM_BOT_TOKEN sozlanmagan")
    return Bot(token=token)


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher
