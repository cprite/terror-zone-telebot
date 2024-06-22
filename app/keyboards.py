from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder



menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Старт", callback_data="start")],
     [InlineKeyboardButton(text="Настроить уведомления", callback_data="config_notifications")],
])
