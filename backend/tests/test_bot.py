"""Bot matnlari, tugmalari va sozlamalari — tarmoqsiz unit testlar."""

from __future__ import annotations

import pytest
from aiogram.types import MenuButtonWebApp

from app.bot.bot import BotNotConfigured, build_bot
from app.bot.texts import language_of, text
from app.bot.ui import app_keyboard, commands, menu_button
from app.core.config import Settings, settings


def test_language_of_defaults_to_uzbek() -> None:
    assert language_of(None) == "uz"
    assert language_of("uz") == "uz"
    assert language_of("en") == "uz"
    assert language_of("ru") == "ru"
    assert language_of("ru-RU") == "ru"


def test_start_text_without_name() -> None:
    assert text("start", "uz", name="").startswith("Salom!")
    assert "Dilnoza" in text("start", "uz", name=" Dilnoza")


def test_commands_are_localized() -> None:
    uz = {command.command for command in commands("uz")}
    ru = {command.command for command in commands("ru")}
    assert uz == ru == {"start", "app"}
    assert commands("uz")[0].description != commands("ru")[0].description


def test_keyboard_and_menu_button_need_webapp_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "webapp_url", "")
    assert app_keyboard("uz") is None
    assert menu_button() is None

    monkeypatch.setattr(settings, "webapp_url", "https://qoshni.example.com/")
    keyboard = app_keyboard("uz")
    assert keyboard is not None
    assert keyboard.inline_keyboard[0][0].web_app.url == "https://qoshni.example.com/"

    button = menu_button()
    assert isinstance(button, MenuButtonWebApp)
    assert button.type == "web_app"


def test_build_bot_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "bot_token", lambda _self: None)
    with pytest.raises(BotNotConfigured):
        build_bot()
