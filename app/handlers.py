from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.methods.delete_message import DeleteMessage

import asyncio
import time

import app.keyboards as kb

from app.src.zone_info import get_terror_zone_info
from app.src.zones import ZONES

router = Router()

global looping
global zone_choice_list
looping = False
zone_choice_list = []


"""
MAIN MENU HANDLERS / CALLBACKS
"""
@router.message(CommandStart())
@router.message(F.text == "Меню")
async def cmd_start(message: Message):
    global looping
    looping = False
    await message.answer("Главное меню",
                        reply_markup=kb.menu)

@router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery):
    await call.message.edit_text("Главное меню",
                                reply_markup=kb.menu)


"""
MAIN POSTING LOOP CALLBACK
"""
@router.callback_query(F.data == "start")
async def back(call: CallbackQuery):
    global looping
    global zone_choice_list
    looping = True

    await call.message.edit_text("В процессе...", reply_markup=kb.menu_button)

    while looping:

        current_time = time.localtime()
        minutes = current_time.tm_min

        if minutes == 45 or minutes == 0:

            next_parts = get_terror_zone_info()
            next = " ".join(next_parts)

            if next in zone_choice_list or not zone_choice_list:

                next_zone = ""

                for zone_b in next_parts:
                    next_zone += "- " + zone_b + "\n"

                if minutes == 45:
                    await call.message.answer(f"!!!ВНИМАНИЕ!!!\n\nЧерез 15 мин начинается:\n{next_zone}")
                elif minutes == 0:
                    await call.message.answer(f"!!!ВПЕРЕД!!!\n\nНачинается зона:\n{next_zone}")

        await asyncio.sleep(60)


"""
TERROR ZONE CHOICE CALLBACKS
"""
@router.callback_query(F.data == "terror_zone_choice")
async def notifications(call: CallbackQuery):
    await call.message.edit_text("Выберите нужные террор-зоны для уведомлений:",
                            reply_markup=await kb.zone_choice())

@router.callback_query(F.data.startswith("zone_"))
async def zone_choice(call: CallbackQuery):
    global zone_choice_list

    terror_zone = ZONES[int(call.data.split("_")[1])].replace("🐮 ", "")

    if terror_zone in zone_choice_list:
        zone_choice_list.remove(terror_zone)
    else:
        zone_choice_list.append(terror_zone)

    await call.message.edit_text("Выберите нужные террор-зоны для уведомлений:",
                            reply_markup=await kb.zone_choice(zone_choice_list))
