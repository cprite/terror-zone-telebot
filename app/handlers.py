from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import asyncio
import time

import app.keyboards as kb

from app.src.zone_info import get_next_terror_zone, get_current_terror_zone
from app.src.zones import ZONES
from app.ui.language import RUSSIAN, ENGLISH, UKRAINIAN, CHINESE, PORTUGUESE, GERMAN
from app.admin.stats.csv.users import add_new_user, get_users, delete_user, switch_looping, switch_all_zones, get_stats

router = Router()

global maintenance_status
maintenance_status = "OFF"


"""
MAIN MENU HANDLERS / CALLBACKS
"""

class GlobalVars(StatesGroup):
    looping = State()
    zone_choice_list = State()
    language = State()
    announcement = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        add_new_user(message.from_user.id)

        await state.update_data(looping=False, zone_choice_list=[], language=ENGLISH)

        data = await state.get_data()
        language = data["language"]

        await message.answer(language["menu"][0],
                            reply_markup=await kb.menu(language, message.from_user.id))

    else: await message.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        await state.update_data(looping=False)
        data = await state.get_data()
        language = data["language"]
        zone_choice_list = data["zone_choice_list"]
        zone_count = len(zone_choice_list)

        switch_looping(message.from_user.id)
        if zone_count == 0 or zone_count == 36:
            switch_all_zones(message.from_user.id)

        await message.answer(language["menu"][0],
                            reply_markup=await kb.menu(language, message.from_user.id))

    else: await message.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "menu")
async def cmd_start(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        await state.update_data(looping=False)
        data = await state.get_data()
        language = data["language"]

        await call.message.edit_text(language["menu"][0],
                            reply_markup=await kb.menu(language, call.from_user.id))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "language")
async def language_selection(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        data = await state.get_data()
        language = data["language"]

        await call.message.edit_text(language["menu"][7],
                                    reply_markup=await kb.language_choice(language))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data.startswith("language_"))
async def set_language(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        language = call.data.split("_")[1]

        if language == "ru":
            await state.update_data(language=RUSSIAN)
        elif language == "en":
            await state.update_data(language=ENGLISH)
        elif language == "uk":
            await state.update_data(language=UKRAINIAN)
        elif language == "zh":
            await state.update_data(language=CHINESE)
        elif language == "pt":
            await state.update_data(language=PORTUGUESE)
        elif language == "de":
            await state.update_data(language=GERMAN)

        data = await state.get_data()

        await call.message.edit_text(data["language"]["menu"][0],
                                    reply_markup=await kb.menu(data["language"], call.from_user.id))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "current_zone")
async def current_zone(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        data = await state.get_data()
        language = data["language"]

        current_parts = get_current_terror_zone()

        current_zone = ""

        for i in current_parts:
            current_zone += "- " + i + "\n"

        await call.message.edit_text(language["menu"][5] + "\n\n" + current_zone,
                                    reply_markup=await kb.back(language))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")


"""
ADMIN PANEL HANDLERS / CALLBACKS
"""

@router.callback_query(F.data == "admin")
async def admin_mode(call: CallbackQuery):
    global maintenance_status

    await call.message.edit_text("Панель админа", reply_markup=await kb.admin_panel(maintenance_status))

@router.callback_query(F.data == "announcement")
async def set_announcement(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data["language"]

    await state.set_state(GlobalVars.announcement)

    await call.message.edit_text("Введите объявление:", reply_markup=await kb.back(language))

@router.message(GlobalVars.announcement)
async def send_announcement(message: Message, state: FSMContext):
    await state.update_data(announcement=message.text)
    users = get_users()

    data = await state.get_data()
    language = data["language"]
    announcement = data["announcement"]

    for user in users:
        try:
            await message.bot.send_message(user, announcement)
        except:
            delete_user(user)

    await message.answer(language["menu"][0],
                                reply_markup=await kb.menu(language, message.from_user.id))

@router.callback_query(F.data == "stats")
async def user_stats(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    language = data["language"]

    user_count = len(get_users())
    stats = get_stats()

    await call.message.edit_text(f"Общее кол-во пользователей: {user_count}\n\nАктивная рассылка: {stats[0]}\n\nВыбраны все зоны: {stats[1]}",
                                 reply_markup=await kb.back(language))

@router.callback_query(F.data == "tech_maintenance")
async def maintenance_mode(call: CallbackQuery):
    global maintenance_status

    if maintenance_status == "OFF":
        maintenance_status = "ON"
    else:
        maintenance_status = "OFF"

    await call.message.edit_text("Панель админа", reply_markup=await kb.admin_panel(maintenance_status))


"""
MAIN POSTING LOOP CALLBACK
"""
@router.callback_query(F.data == "start")
async def back(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        await state.update_data(looping=True)

        data = await state.get_data()

        zone_choice_list = data["zone_choice_list"]
        zone_count = len(zone_choice_list)
        language = data["language"]
        looping = data["looping"]

        switch_looping(call.from_user.id)
        if zone_count == 0 or zone_count == 36:
            switch_all_zones(call.from_user.id)

        await call.message.edit_text(language["main_loop"][0])

        while looping:

            current_time = time.localtime()
            minutes = current_time.tm_min
            seconds = current_time.tm_sec

            if minutes == 45 or minutes == 0:

                next_parts = get_next_terror_zone()
                next = " ".join(next_parts)

                if next in zone_choice_list or not zone_choice_list:

                    next_zone = ""

                    for zone_b in next_parts:
                        next_zone += "- " + zone_b + "\n"

                    if minutes == 45 and seconds == 0:
                        await call.message.answer(language["main_loop"][1] + "\n" + next_zone + "\n\n" + "@terror_zone_bot")
                    elif minutes == 0 and seconds == 0:
                        await call.message.answer(language["main_loop"][2] + "\n" + next_zone + "\n\n" + "@terror_zone_bot")

            if maintenance_status == "ON":
                await call.message.edit_text("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")
                await state.update_data(looping=False)
                break

            data = await state.get_data()
            looping = data["looping"]

            await asyncio.sleep(1)

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")


"""
TERROR ZONE CHOICE CALLBACKS
"""

@router.callback_query(F.data == "terror_zone_choice")
async def notifications(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        data = await state.get_data()
        language = data["language"]
        zone_choice_list = data["zone_choice_list"]

        await call.message.edit_text(language["zone_choice"][0],
                                reply_markup=await kb.zone_choice(language, zone_choice_list))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data.startswith("zone_"))
async def zone_choice(call: CallbackQuery, state: FSMContext):
    global maintenance_status

    if maintenance_status == "OFF":

        data = await state.get_data()
        language = data["language"]
        zone_choice_list = data["zone_choice_list"]

        terror_zone = ZONES[int(call.data.split("_")[1])].replace("🐮 ", "")

        if terror_zone in zone_choice_list:
            zone_choice_list.remove(terror_zone)
        else:
            zone_choice_list.append(terror_zone)

        await state.update_data(zone_choice_list=zone_choice_list)
        data = await state.get_data()
        zone_choice_list = data["zone_choice_list"]

        await call.message.edit_text(language["zone_choice"][0],
                                reply_markup=await kb.zone_choice(language, zone_choice_list))

    else: await call.answer("Бот находится на техническом обслуживании. Пожалуйста, попробуйте позже.")
