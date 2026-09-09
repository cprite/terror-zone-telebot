"""End-to-end through a real Dispatcher, with the Telegram API faked out.

The unit tests above never let a handler run to completion, so they would not
notice a dependency-injection mistake - a handler asking for `storage` that
aiogram cannot supply fails only at runtime, on the first /start.
"""

from __future__ import annotations

import datetime as dt

import pytest
from aiogram import Bot
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from tzbot.bot import build_dispatcher
from tzbot.config import Settings
from tzbot.providers.base import Snapshot

USER_ID = 555
ADMIN_ID = 1000


class RecordingBot(Bot):
    """A Bot that answers every API call locally and remembers what was sent."""

    def __init__(self) -> None:
        super().__init__(token="42:TEST")
        self.calls: list[object] = []

    async def __call__(self, method, request_timeout=None):  # type: ignore[override]
        self.calls.append(method)
        chat = Chat(id=USER_ID, type="private")
        if isinstance(method, (SendMessage, EditMessageText)):
            return Message(
                message_id=len(self.calls),
                date=dt.datetime.now(dt.UTC),
                chat=chat,
                text=getattr(method, "text", ""),
            )
        return True

    def texts(self) -> list[str]:
        return [
            m.text for m in self.calls if isinstance(m, (SendMessage, EditMessageText))
        ]

    def alerts(self) -> list[str]:
        return [m.text or "" for m in self.calls if isinstance(m, AnswerCallbackQuery)]


def _user(user_id: int, language_code: str = "ru") -> User:
    return User(id=user_id, is_bot=False, first_name="T", language_code=language_code)


def _message(text: str, user_id: int = USER_ID, language_code: str = "ru") -> Update:
    user = _user(user_id, language_code)
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=dt.datetime.now(dt.UTC),
            chat=Chat(id=user_id, type="private"),
            from_user=user,
            text=text,
        ),
    )


def _callback(data: str, user_id: int = USER_ID) -> Update:
    user = _user(user_id)
    return Update(
        update_id=2,
        callback_query=CallbackQuery(
            id="1",
            from_user=user,
            chat_instance="1",
            data=data,
            message=Message(
                message_id=1,
                date=dt.datetime.now(dt.UTC),
                chat=Chat(id=user_id, type="private"),
                from_user=user,
                text="menu",
            ),
        ),
    )


class StubTracker:
    snapshot = Snapshot(
        current_raw="Durance of Hate", next_raw="Dark Wood and Underground Passage"
    )


@pytest.fixture
def bot():
    return RecordingBot()


@pytest.fixture
def dispatcher(storage):
    settings = Settings(BOT_TOKEN="42:TEST", ADMIN_IDS=str(ADMIN_ID))
    return build_dispatcher(
        settings, storage, tracker=StubTracker(), broadcaster=None
    )


async def test_start_registers_the_user_and_shows_the_menu(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))

    assert "Главное меню" in bot.texts()[0]
    assert await storage.all_active_ids() == [USER_ID]
    # Language came from the Telegram client.
    assert await storage.get_language(USER_ID) == "ru"


async def test_unsupported_client_language_falls_back_to_english(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start", language_code="sv"))
    assert await storage.get_language(USER_ID) == "en"


async def test_subscription_toggles_both_ways(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))

    await dispatcher.feed_update(bot, _callback("subscription:toggle"))
    assert await storage.is_subscribed(USER_ID) is True

    await dispatcher.feed_update(bot, _callback("subscription:toggle"))
    assert await storage.is_subscribed(USER_ID) is False


async def test_zone_filter_survives_the_round_trip(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))
    await dispatcher.feed_update(bot, _callback("zones:open"))
    await dispatcher.feed_update(bot, _callback("zones:toggle:26"))

    assert await storage.zone_filter(USER_ID) == {26}


async def test_garbage_zone_id_is_ignored(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))
    await dispatcher.feed_update(bot, _callback("zones:toggle:not-a-number"))

    assert await storage.zone_filter(USER_ID) == set()


async def test_current_zone_shows_both_zones(dispatcher, bot):
    await dispatcher.feed_update(bot, _message("/start"))
    await dispatcher.feed_update(bot, _callback("zone:current"))

    body = bot.texts()[-1]
    assert "Durance of Hate" in body
    assert "Dark Wood and Underground Passage" in body


async def test_language_switch_changes_the_menu(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))
    await dispatcher.feed_update(bot, _callback("language:set:de"))

    assert await storage.get_language(USER_ID) == "de"
    assert "Hauptmenü" in bot.texts()[-1]


async def test_unknown_language_code_is_rejected(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start"))
    await dispatcher.feed_update(bot, _callback("language:set:klingon"))

    assert await storage.get_language(USER_ID) == "ru"


async def test_maintenance_turns_users_away_but_not_admins(dispatcher, bot, storage):
    await storage.set_maintenance(True)

    # A first-ever /start during maintenance has no stored language, so the
    # notice follows the Telegram client language instead of defaulting to English.
    await dispatcher.feed_update(bot, _message("/start", user_id=USER_ID))
    assert any("обслуживании" in text for text in bot.texts())
    assert await storage.all_active_ids() == []  # the handler never ran

    await dispatcher.feed_update(bot, _message("/start", user_id=ADMIN_ID))
    assert any("Главное меню" in text for text in bot.texts())


async def test_maintenance_notice_falls_back_to_english(dispatcher, bot, storage):
    await storage.set_maintenance(True)
    await dispatcher.feed_update(bot, _message("/start", language_code="sv"))
    assert any("under maintenance" in text for text in bot.texts())


async def test_admin_sees_the_panel_button_and_a_user_does_not(dispatcher, bot):
    await dispatcher.feed_update(bot, _message("/start", user_id=ADMIN_ID))
    admin_markup = bot.calls[-1].reply_markup
    labels = [b.text for row in admin_markup.inline_keyboard for b in row]
    assert "Admin panel" in labels

    await dispatcher.feed_update(bot, _message("/start", user_id=USER_ID))
    user_markup = bot.calls[-1].reply_markup
    labels = [b.text for row in user_markup.inline_keyboard for b in row]
    assert "Admin panel" not in labels


async def test_admin_stats_render(dispatcher, bot, storage):
    await dispatcher.feed_update(bot, _message("/start", user_id=ADMIN_ID))
    await dispatcher.feed_update(bot, _callback("admin:open", user_id=ADMIN_ID))
    await dispatcher.feed_update(bot, _callback("admin:stats", user_id=ADMIN_ID))

    assert "Users total: 1" in bot.texts()[-1]
