"""Bot tugmalari va buyruqlar ro'yxati — Mini App manzili settings'dan olinadi."""

from __future__ import annotations

from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    WebAppInfo,
)

from app.bot.texts import text
from app.core.config import settings


def app_keyboard(language: str) -> InlineKeyboardMarkup | None:
    """Xabar ostidagi Mini App tugmasi; manzil bo'lmasa None."""
    if not settings.webapp_url:
        return None
    button = InlineKeyboardButton(
        text=text("open", language),
        web_app=WebAppInfo(url=settings.webapp_url),
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])


def menu_button() -> MenuButtonWebApp | None:
    """Chat menyudagi doimiy tugma (BotFather'dagi "menu button" almashinuvchisi)."""
    if not settings.webapp_url:
        return None
    return MenuButtonWebApp(
        type="web_app",
        text=text("open", "uz"),
        web_app=WebAppInfo(url=settings.webapp_url),
    )


def commands(language: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=text("start_desc", language)),
        BotCommand(command="app", description=text("app_desc", language)),
    ]


def command_scopes() -> list[tuple[BotCommandScopeAllPrivateChats, list[BotCommand], str]]:
    """Har til uchun alohida ro'yxat — Telegram `/help` menyu tilga mos ko'rsatadi."""
    scope = BotCommandScopeAllPrivateChats()
    return [(scope, commands(language), language) for language in ("uz", "ru")]
