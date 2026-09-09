"""Access control.

The previous version checked admin rights only where it *drew* the admin
button, never where it acted.  A callback query is not proof that the user was
shown the button: a client speaking MTProto directly can send arbitrary
callback data to any message the bot has posted with an inline keyboard, so
every admin action was reachable by any user who had ever talked to the bot.

The fix is structural rather than per-handler: the admin router installs this
filter on both its message and callback observers, so a handler cannot be added
to it without inheriting the check.
"""

from __future__ import annotations

from collections.abc import Container

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject, User


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids: Container[int]) -> None:
        self._admin_ids = admin_ids

    async def __call__(self, event: TelegramObject) -> bool:
        user: User | None = getattr(event, "from_user", None)
        if user is None and isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        return user is not None and user.id in self._admin_ids
