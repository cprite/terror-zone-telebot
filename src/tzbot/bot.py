"""Wiring: build the dispatcher, run the polling loop alongside the tracker."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from tzbot.config import Settings
from tzbot.handlers import admin, user
from tzbot.middlewares import MaintenanceMiddleware
from tzbot.providers import D2RunewizardProvider
from tzbot.providers.base import TerrorZoneProvider
from tzbot.storage import Storage
from tzbot.tracker import Broadcaster, Tracker

log = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="start", description="Start the bot"),
    BotCommand(command="menu", description="Open the main menu"),
]


def build_provider(settings: Settings) -> TerrorZoneProvider:
    return D2RunewizardProvider(
        contact=settings.d2rw_contact,
        platform=settings.d2rw_platform,
        repo=settings.d2rw_repo,
        token=settings.d2rw_token,
    )


def build_dispatcher(
    settings: Settings, storage: Storage, tracker: Tracker, broadcaster: Broadcaster
) -> Dispatcher:
    admin_ids = frozenset(settings.admin_ids)

    dispatcher = Dispatcher()
    # Anything put here is passed to handlers that declare a matching argument.
    dispatcher["storage"] = storage
    dispatcher["tracker"] = tracker
    dispatcher["broadcaster"] = broadcaster
    dispatcher["admin_ids"] = admin_ids

    user_router = user.build_router()
    maintenance = MaintenanceMiddleware(storage, admin_ids)
    user_router.message.middleware(maintenance)
    user_router.callback_query.middleware(maintenance)

    # Admin first: its guard rejects everyone else, and the user router has no
    # handler for admin:* callbacks anyway.
    dispatcher.include_router(admin.build_router(admin_ids))
    dispatcher.include_router(user_router)
    return dispatcher


async def run(settings: Settings) -> None:
    storage = Storage(settings.database_path)
    await storage.connect()

    bot = Bot(token=settings.bot_token)
    provider = build_provider(settings)
    broadcaster = Broadcaster(bot, storage, rate=settings.broadcast_rate)
    tracker = Tracker(
        provider,
        storage,
        broadcaster,
        poll_interval=settings.poll_interval,
        prealert_minute=settings.prealert_minute,
    )
    dispatcher = build_dispatcher(settings, storage, tracker, broadcaster)

    if not settings.admin_ids:
        log.warning("ADMIN_IDS is empty - the admin panel is unreachable by design")

    try:
        await bot.set_my_commands(COMMANDS)
        tracker.start()
        await dispatcher.start_polling(bot, handle_signals=True)
    finally:
        await tracker.stop()
        await provider.close()
        await storage.close()
        await bot.session.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    from tzbot.config import load_settings

    try:
        asyncio.run(run(load_settings()))
    except KeyboardInterrupt:
        log.info("stopped")
