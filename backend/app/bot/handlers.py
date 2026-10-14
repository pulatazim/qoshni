"""Bot handlerlari: /start, /app, /help."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.texts import language_of, text
from app.bot.ui import app_keyboard

router = Router()


def _language(message: Message) -> str:
    return language_of(message.from_user.language_code if message.from_user else None)


def _name(message: Message) -> str:
    first = message.from_user.first_name if message.from_user else None
    return f" {first}" if first else ""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    language = _language(message)
    await message.answer(
        text("start", language, name=_name(message)),
        reply_markup=app_keyboard(language),
    )


@router.message(Command("app"))
async def cmd_app(message: Message) -> None:
    language = _language(message)
    keyboard = app_keyboard(language)
    key = "open" if keyboard is not None else "no_app"
    await message.answer(text(key, language), reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(text("help", _language(message)))
