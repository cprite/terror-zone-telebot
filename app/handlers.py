from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import asyncio
import time

import app.keyboards as kb

from app.src.scraping import get_terror_zone_info

router = Router()

global looping
looping = False


@router.message(CommandStart())
async def cmd_start(message: Message):
    global looping
    looping = False

    await message.answer("Главное меню",
                        reply_markup=kb.menu)

@router.message(F.text == "Меню")
async def cmd_start(message: Message):
    global looping
    looping = False

    await message.answer("Главное меню",
                        reply_markup=kb.menu)


@router.callback_query(F.data == "start")
async def back(call: CallbackQuery):
    global looping
    looping = True

    while looping:
        await call.message.edit_text("В процессе...")

        current_time = time.localtime()

        if current_time.tm_min == 0:
            current, next = get_terror_zone_info()

            current_zone = ""
            next_zone = ""
            for zone_a in current:
                current_zone += "- " + zone_a + "\n"

            for zone_b in next:
                next_zone += "- " + zone_b + "\n"

            await call.message.answer(f"Текущая зона:\n{current_zone}\nСледующая зона:\n{next_zone}")

        await asyncio.sleep(60)
