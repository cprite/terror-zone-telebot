from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import asyncio
import time

import app.keyboards as kb

from app.src.zone_info import get_terror_zone_info
from app.src.zones import ZONES
from app.ui.language import RUSSIAN, ENGLISH

router = Router()


"""
MAIN MENU HANDLERS / CALLBACKS
"""

class GlobalVars(StatesGroup):
    looping = State()
    zone_choice_list = State()
    language = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.update_data(looping=False, zone_choice_list=[], language=ENGLISH)

    data = await state.get_data()
    language = data["language"]

    await message.answer(language["menu"][0],
                        reply_markup=await kb.menu(language))

@router.message(Command("stop"))
async def cmd_start(message: Message, state: FSMContext):
    await state.update_data(looping=False)
    data = await state.get_data()
    language = data["language"]

    await message.answer(language["menu"][0],
                        reply_markup=await kb.menu(language))

@router.callback_query(F.data == "menu")
async def cmd_start(call: CallbackQuery, state: FSMContext):
    await state.update_data(looping=False)
    data = await state.get_data()
    language = data["language"]

    await call.message.edit_text(language["menu"][0],
                        reply_markup=await kb.menu(language))

@router.callback_query(F.data == "language")
async def language_selection(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data["language"]

    if language == RUSSIAN:
        await state.update_data(language=ENGLISH)
    else:
        await state.update_data(language=RUSSIAN)

    data = await state.get_data()
    language = data["language"]

    await call.message.edit_text(language["menu"][0],
                                reply_markup=await kb.menu(language))


"""
MAIN POSTING LOOP CALLBACK
"""
@router.callback_query(F.data == "start")
async def back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    zone_choice_list = data["zone_choice_list"]
    language = data["language"]
    await state.update_data(looping=True)
    looping = data["looping"]

    await call.message.edit_text(language["main_loop"][0])

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

        data = await state.get_data()
        looping = data["looping"]
        print("loop")

        await asyncio.sleep(0.1)


"""
TERROR ZONE CHOICE CALLBACKS
"""
@router.callback_query(F.data == "terror_zone_choice")
async def notifications(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data["language"]
    zone_choice_list = data["zone_choice_list"]

    await call.message.edit_text(language["zone_choice"][0],
                            reply_markup=await kb.zone_choice(language, zone_choice_list))

@router.callback_query(F.data.startswith("zone_"))
async def zone_choice(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data["language"]
    zone_choice_list = data["zone_choice_list"]

    terror_zone = ZONES[int(call.data.split("_")[1])].replace("🐮 ", "")

    if terror_zone in zone_choice_list:
        zone_choice_list.remove(terror_zone)
    else:
        zone_choice_list.append(terror_zone)

    await state.update_data(zone_choice_list=zone_choice_list)

    await call.message.edit_text(language["zone_choice"][0],
                            reply_markup=await kb.zone_choice(language, zone_choice_list))
