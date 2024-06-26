from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


from app.src.zones import ZONES


"""
MAIN MENU KEYBOARDS
"""
async def menu(language):
    menu_keyboard = InlineKeyboardBuilder()
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][1], callback_data="start"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][2], callback_data="terror_zone_choice"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][3], callback_data="current_zone"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][4], callback_data="language"))

    return menu_keyboard.adjust(2).as_markup()

async def back(language):
    back_keyboard = InlineKeyboardBuilder()
    back_keyboard.add(InlineKeyboardButton(text=language['menu'][6], callback_data="menu"))

    return back_keyboard.as_markup()


"""
ZONE CHOICE KEYBOARDS
"""
async def zone_choice(language, zone_choice_list):
    keyboard = InlineKeyboardBuilder()

    for index, zone in ZONES.items():
        if zone.replace("🐮 ", "") in zone_choice_list:
            keyboard.add(InlineKeyboardButton(text=f"✅ {zone}", callback_data=f"zone_{str(index)}"))
        else:
            keyboard.add(InlineKeyboardButton(text=zone, callback_data=f"zone_{str(index)}"))

    keyboard.add(InlineKeyboardButton(text=language["zone_choice"][1], callback_data="menu"))

    return keyboard.adjust(3).as_markup()
