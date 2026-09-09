"""Regression tests for the admin panel access hole.

Before this rewrite the admin handlers checked nothing: rights were verified
only where the "Admin panel" button was drawn.  Callback data is attacker
controlled - a client speaking MTProto can post any callback data to any
message the bot has sent with an inline keyboard - so every admin action
(broadcast to the whole user base, set an advert, toggle maintenance) was open
to any user who had ever pressed a button.
"""

from __future__ import annotations

import datetime as dt

import pytest
from aiogram import Bot
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from tzbot.bot import build_dispatcher
from tzbot.config import Settings
from tzbot.filters import IsAdmin
from tzbot.handlers import admin

ADMIN_ID = 1000
INTRUDER_ID = 2000

ADMIN_CALLBACKS = [
    "admin:open",
    "admin:stats",
    "admin:maintenance",
    "admin:announce",
    "admin:ads",
    "admin:ads:set",
    "admin:ads:delete",
]


def _callback(data: str, user_id: int) -> Update:
    user = User(id=user_id, is_bot=False, first_name="T")
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1, date=dt.datetime.now(dt.UTC), chat=chat, from_user=user, text="x"
    )
    return Update(
        update_id=1,
        callback_query=CallbackQuery(
            id="1", from_user=user, chat_instance="1", data=data, message=message
        ),
    )


@pytest.fixture
def bot():
    return Bot(token="42:TEST")


@pytest.fixture
def dispatcher(storage):
    settings = Settings(
        BOT_TOKEN="42:TEST",
        ADMIN_IDS=str(ADMIN_ID),
        DATABASE_PATH=":memory:",
    )
    return build_dispatcher(settings, storage, tracker=None, broadcaster=None)


@pytest.mark.parametrize("data", ADMIN_CALLBACKS)
async def test_intruder_cannot_reach_admin_callbacks(dispatcher, bot, data):
    result = await dispatcher.feed_update(bot, _callback(data, INTRUDER_ID))
    assert result is UNHANDLED, f"{data} was reachable by a non-admin"


@pytest.mark.parametrize("observer_name", ["message", "callback_query"])
async def test_guard_sits_on_the_router_not_on_each_handler(observer_name):
    """Router-level filters run before any handler, so a new one inherits them."""
    router = admin.build_router(frozenset({ADMIN_ID}))
    observer = getattr(router, observer_name)

    allowed, _ = await observer.check_root_filters(
        _callback("admin:open", ADMIN_ID).callback_query
    )
    refused, _ = await observer.check_root_filters(
        _callback("admin:open", INTRUDER_ID).callback_query
    )
    assert allowed and not refused


@pytest.mark.parametrize(
    ("user_id", "allowed"), [(ADMIN_ID, True), (INTRUDER_ID, False), (0, False)]
)
async def test_is_admin_filter(user_id, allowed):
    filt = IsAdmin(frozenset({ADMIN_ID}))
    update = _callback("admin:open", user_id)
    assert await filt(update.callback_query) is allowed
