from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


from app.src.zones import ZONES


menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Старт", callback_data="start")],
     [InlineKeyboardButton(text="Выбор зоны", callback_data="terror_zone_choice")]
])

async def zone_choice(zone_choice_list=[]):
    keyboard = InlineKeyboardBuilder()

    for index, zone in ZONES.items():
        if zone in zone_choice_list:
            keyboard.add(InlineKeyboardButton(text=f"✅ {zone}", callback_data=f"zone_{str(index)}"))
        else:
            keyboard.add(InlineKeyboardButton(text=zone, callback_data=f"zone_{str(index)}"))

    keyboard.add(InlineKeyboardButton(text="Готово", callback_data="menu"))

    return keyboard.adjust(3).as_markup()
