from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


from app.src.zone.zones import ZONES
from app.admin.admin_list import ADMINS


"""
MAIN MENU KEYBOARDS
"""
async def menu(language, user_id):
    menu_keyboard = InlineKeyboardBuilder()
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][1], callback_data="start"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][2], callback_data="terror_zone_choice"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][3], callback_data="current_zone"))
    menu_keyboard.add(InlineKeyboardButton(text=language['menu'][4], callback_data="language"))

    if user_id in ADMINS:
        menu_keyboard.add(InlineKeyboardButton(text="Панель админа", callback_data="admin"))

    return menu_keyboard.adjust(2).as_markup()

async def back(language):
    back_keyboard = InlineKeyboardBuilder()
    back_keyboard.add(InlineKeyboardButton(text=language['menu'][6], callback_data="menu"))

    return back_keyboard.as_markup()

async def language_choice(language):
    language_keyboard = InlineKeyboardBuilder()
    language_keyboard.add(InlineKeyboardButton(text="🇷🇺", callback_data="language_ru"))
    language_keyboard.add(InlineKeyboardButton(text="🇬🇧", callback_data="language_en"))
    language_keyboard.add(InlineKeyboardButton(text="🇺🇦", callback_data="language_uk"))
    language_keyboard.add(InlineKeyboardButton(text="🇨🇳", callback_data="language_zh"))
    language_keyboard.add(InlineKeyboardButton(text="🇧🇷", callback_data="language_pt"))
    language_keyboard.add(InlineKeyboardButton(text="🇩🇪", callback_data="language_de"))

    language_keyboard.add(InlineKeyboardButton(text=language['menu'][6], callback_data="menu"))

    return language_keyboard.adjust(2).as_markup()


"""
ADMIN PANELS KEYBOARDS
"""
async def back_admin():
    back_keyboard = InlineKeyboardBuilder()
    back_keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin"))

    return back_keyboard.as_markup()

async def admin_panel(maintenance_status):
    admin_panel_keyboard = InlineKeyboardBuilder()
    admin_panel_keyboard.add(InlineKeyboardButton(text="Объявление", callback_data="announcement"))
    admin_panel_keyboard.add(InlineKeyboardButton(text=f"Тех. работы: {maintenance_status}", callback_data="tech_maintenance"))
    admin_panel_keyboard.add(InlineKeyboardButton(text=f"Интеграция", callback_data="ads"))
    admin_panel_keyboard.add(InlineKeyboardButton(text=f"Статистика", callback_data="stats"))
    admin_panel_keyboard.add(InlineKeyboardButton(text=f"Назад", callback_data="menu"))

    return admin_panel_keyboard.adjust(2).as_markup()

async def ads_panel(ads_status):
    adjust = 1
    ads_panel_keyboard = InlineKeyboardBuilder()
    ads_panel_keyboard.add(InlineKeyboardButton(text=f"Добавить новую", callback_data="ads_add"))

    if ads_status:
        ads_panel_keyboard.add(InlineKeyboardButton(text=f"Удалить текущую", callback_data="ads_delete"))
        adjust = 2

    ads_panel_keyboard.add(InlineKeyboardButton(text=f"Назад", callback_data="admin"))

    return ads_panel_keyboard.adjust(adjust).as_markup()


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
