"""Inline keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tzbot.i18n import LANGUAGES, flag, t
from tzbot.zones import ZONES


def menu(language: str, *, subscribed: bool, is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle = "btn_unsubscribe" if subscribed else "btn_subscribe"
    builder.button(text=t(language, toggle), callback_data="subscription:toggle")
    builder.button(text=t(language, "btn_zones"), callback_data="zones:open")
    builder.button(text=t(language, "btn_current"), callback_data="zone:current")
    builder.button(text=t(language, "btn_language"), callback_data="language:open")
    if is_admin:
        builder.button(text="Admin panel", callback_data="admin:open")
    builder.adjust(2)
    return builder.as_markup()


def back(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_back"), callback_data="menu:open")
    return builder.as_markup()


def language_choice(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in LANGUAGES:
        builder.button(text=flag(code), callback_data=f"language:set:{code}")
    builder.button(text=t(language, "btn_back"), callback_data="menu:open")
    builder.adjust(3)
    return builder.as_markup()


def zone_choice(language: str, selected: set[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for zone in ZONES:
        mark = "\N{WHITE HEAVY CHECK MARK} " if zone.id in selected else ""
        builder.button(text=f"{mark}{zone.label}", callback_data=f"zones:toggle:{zone.id}")
    builder.button(text=t(language, "btn_done"), callback_data="menu:open")
    builder.adjust(1)
    return builder.as_markup()


# ------------------------------------------------------------------- admin

def admin_panel(*, maintenance: bool, advert_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Announcement", callback_data="admin:announce")
    builder.button(
        text=f"Maintenance: {'ON' if maintenance else 'OFF'}",
        callback_data="admin:maintenance",
    )
    builder.button(text="Advert", callback_data="admin:ads")
    builder.button(text="Stats", callback_data="admin:stats")
    builder.button(text="Back", callback_data="menu:open")
    builder.adjust(2)
    return builder.as_markup()


def ads_panel(*, advert_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Set new advert", callback_data="admin:ads:set")
    if advert_active:
        builder.button(text="Delete current", callback_data="admin:ads:delete")
    builder.button(text="Back", callback_data="admin:open")
    builder.adjust(1)
    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Back", callback_data="admin:open")]]
    )
