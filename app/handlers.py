from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.methods.delete_message import DeleteMessage

import asyncio
import time

import app.keyboards as kb

from app.src.zone_info import get_terror_zone_info
from app.src.zones import ZONES
from app.ui.language import RUSSIAN, ENGLISH

router = Router()

# Global / default variables
global looping
global zone_choice_list
global language
looping = False
zone_choice_list = []
language = RUSSIAN


"""
MAIN MENU HANDLERS / CALLBACKS
"""
@router.message(CommandStart())
@router.message(F.text == "Menu")
@router.message(F.text == "Меню")
async def cmd_start(message: Message):
    global looping
    global language
    looping = False
    await message.answer(language["menu"][0],
                        reply_markup=await kb.menu(language))

@router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery):
    global language
    await call.message.edit_text(language["menu"][0],
                                reply_markup=await kb.menu(language))

@router.callback_query(F.data == "language")
async def language_selection(call: CallbackQuery):
    global language

    if language == RUSSIAN:
        language = ENGLISH
    else:
        language = RUSSIAN

    await call.message.edit_text(language["menu"][0],
                                reply_markup=await kb.menu(language))


"""
MAIN POSTING LOOP CALLBACK
"""
@router.callback_query(F.data == "start")
async def back(call: CallbackQuery):
    global looping
    global zone_choice_list
    global language
    looping = True

    await call.message.answer(language["main_loop"][0], reply_markup=await kb.menu_button(language))

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
                    await call.message.answer(language["main_loop"][1] + "\n" + next_zone)
                elif minutes == 0:
                    await call.message.answer(language["main_loop"][2] + "\n" + next_zone)

        await asyncio.sleep(60)


"""
TERROR ZONE CHOICE CALLBACKS
"""
@router.callback_query(F.data == "terror_zone_choice")
async def notifications(call: CallbackQuery):
    global zone_choice_list
    global language
    await call.message.edit_text(language["zone_choice"][0],
                            reply_markup=await kb.zone_choice(language, zone_choice_list))

@router.callback_query(F.data.startswith("zone_"))
async def zone_choice(call: CallbackQuery):
    global zone_choice_list
    global language

    terror_zone = ZONES[int(call.data.split("_")[1])].replace("🐮 ", "")

    if terror_zone in zone_choice_list:
        zone_choice_list.remove(terror_zone)
    else:
        zone_choice_list.append(terror_zone)

    await call.message.edit_text(language["zone_choice"][0],
                            reply_markup=await kb.zone_choice(language, zone_choice_list))
