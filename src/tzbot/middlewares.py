"""Middlewares shared by the user-facing routers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Container
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from tzbot.i18n import LANGUAGES, t
from tzbot.storage import Storage


class MaintenanceMiddleware(BaseMiddleware):
    """Turns the bot away from everyone except admins while maintenance is on."""

    def __init__(self, storage: Storage, admin_ids: Container[int]) -> None:
        self._storage = storage
        self._admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None and user.id in self._admin_ids:
            return await handler(event, data)

        if not await self._storage.maintenance():
            return await handler(event, data)

        notice = t(await self._language_for(user), "maintenance")
        if isinstance(event, CallbackQuery):
            await event.answer(notice, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(notice)
        return None

    async def _language_for(self, user: User | None) -> str:
        """Answer in the user's language even if they are not in the database yet.

        Someone whose first ever /start lands during maintenance has no stored
        preference, so fall back to their Telegram client language.
        """
        if user is None:
            return "en"
        stored = await self._storage.get_language(user.id)
        if stored != "en":
            return stored
        client = ((user.language_code or "").split("-")[0])
        return client if client in LANGUAGES else "en"
