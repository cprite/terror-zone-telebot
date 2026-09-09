"""Polling the tracker once for everybody, and fanning rotations out.

The original design ran ``while True`` *inside a callback handler*, one task per
user, each waking every second and re-reading a file, with the subscription
state living in that task's memory.  Restarting the process dropped every
subscription silently, and a thousand users meant a thousand loops.

Here a single task polls the provider, and notifications are driven by what the
provider reports rather than by each user's wall clock.
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from tzbot.i18n import t
from tzbot.providers.base import ProviderError, Snapshot, TerrorZoneProvider
from tzbot.storage import Storage

log = logging.getLogger(__name__)


class Broadcaster:
    """Sends one message to many chats without tripping Telegram's rate limit."""

    def __init__(self, bot: Bot, storage: Storage, rate: float = 25.0) -> None:
        if rate <= 0:
            raise ValueError(f"broadcast rate must be positive, got {rate!r}")
        self._bot = bot
        self._storage = storage
        self._delay = 1.0 / rate

    async def send(self, user_id: int, text: str) -> bool:
        """Deliver one message. Returns False if the user is gone for good."""
        try:
            await self._bot.send_message(user_id, text)
            return True
        except TelegramRetryAfter as exc:
            log.warning("flood control: sleeping %ss", exc.retry_after)
            await asyncio.sleep(exc.retry_after)
            return await self.send(user_id, text)
        except TelegramForbiddenError:
            # Blocked the bot, or deleted the chat. Stop writing to them.
            log.info("user %s is unreachable, deactivating", user_id)
            await self._storage.deactivate(user_id)
            return False
        except TelegramBadRequest as exc:
            # "chat not found" and friends: also terminal for this chat.
            log.info("user %s rejected the message (%s), deactivating", user_id, exc)
            await self._storage.deactivate(user_id)
            return False
        except Exception:
            # A transient failure must NOT cost the user their subscription.
            log.exception("transient failure sending to %s", user_id)
            return True

    async def fan_out(self, messages: dict[int, str]) -> int:
        delivered = 0
        for user_id, text in messages.items():
            if await self.send(user_id, text):
                delivered += 1
            await asyncio.sleep(self._delay)
        return delivered


class Tracker:
    def __init__(
        self,
        provider: TerrorZoneProvider,
        storage: Storage,
        broadcaster: Broadcaster,
        *,
        poll_interval: int = 60,
        prealert_minute: int = 45,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._broadcaster = broadcaster
        self._poll_interval = poll_interval
        self._prealert_minute = prealert_minute

        self._snapshot: Snapshot | None = None
        self._last_prealert: tuple[int, int] | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def snapshot(self) -> Snapshot | None:
        return self._snapshot

    # ------------------------------------------------------------ lifecycle

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="tz-tracker")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        while True:
            try:
                await self.tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("tracker tick failed")
            await asyncio.sleep(self._poll_interval)

    # ----------------------------------------------------------------- work

    async def tick(self, now: dt.datetime | None = None) -> None:
        now = now or dt.datetime.now(dt.UTC)
        try:
            fresh = await self._provider.fetch()
        except ProviderError as exc:
            log.warning("provider %s unavailable: %s", self._provider.name, exc)
            return

        if fresh.current is None and fresh.current_raw:
            # Not fatal: we still relay the raw name, but this is how we learn
            # that the upstream renamed a zone.
            log.warning("unrecognised zone name from provider: %r", fresh.current_raw)

        previous, self._snapshot = self._snapshot, fresh

        if previous is None:
            log.info("tracker primed: now %r, next %r", fresh.current_raw, fresh.next_raw)
            return

        if previous.current_raw != fresh.current_raw:
            log.info("rotation: %r -> %r", previous.current_raw, fresh.current_raw)
            await self._announce_rotation(fresh)
            return

        await self._maybe_prealert(fresh, now)

    async def _maybe_prealert(self, snapshot: Snapshot, now: dt.datetime) -> None:
        """Warn once per hour, shortly before the zone rotates."""
        if now.minute < self._prealert_minute or not snapshot.next_raw:
            return
        stamp = (now.date().toordinal(), now.hour)
        if self._last_prealert == stamp:
            return
        self._last_prealert = stamp
        await self._announce(snapshot, key="prealert", label=snapshot.next_label(),
                             zone_id=snapshot.next.id if snapshot.next else None)

    async def _announce_rotation(self, snapshot: Snapshot) -> None:
        await self._announce(snapshot, key="rotation", label=snapshot.current_label(),
                             zone_id=snapshot.current.id if snapshot.current else None)

    async def _announce(
        self, snapshot: Snapshot, *, key: str, label: str, zone_id: int | None
    ) -> None:
        if await self._storage.maintenance():
            log.info("maintenance is on, skipping %s broadcast", key)
            return

        advert = await self._storage.advert()
        messages: dict[int, str] = {}
        for subscriber in await self._storage.subscribers():
            if not subscriber.wants(zone_id):
                continue
            body = f"{t(subscriber.language, key)}\n\n- {label}"
            if advert:
                body = f"{body}\n\n-----------\n{advert}"
            messages[subscriber.user_id] = body

        if not messages:
            return
        delivered = await self._broadcaster.fan_out(messages)
        log.info("%s broadcast delivered to %s/%s", key, delivered, len(messages))
