"""Delivery semantics.

The bug being pinned here: the old code wrapped every send in a bare ``except``
that deleted the user.  One network blip and a subscriber was gone, with their
zone choices, and nothing said so.
"""

from __future__ import annotations

import pytest
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from tzbot.tracker import Broadcaster


class FakeBot:
    def __init__(self, *, fail_with: dict[int, Exception] | None = None) -> None:
        self.sent: list[tuple[int, str]] = []
        self._fail_with = fail_with or {}
        self._raised: set[int] = set()

    async def send_message(self, chat_id: int, text: str) -> None:
        error = self._fail_with.get(chat_id)
        if error is not None and chat_id not in self._raised:
            self._raised.add(chat_id)
            raise error
        self.sent.append((chat_id, text))


def method_error(cls, message: str):
    return cls(method=object(), message=message)


async def test_delivers_to_everyone(storage):
    bot = FakeBot()
    await storage.ensure_user(1)
    await storage.ensure_user(2)

    delivered = await Broadcaster(bot, storage, rate=10_000).fan_out({1: "a", 2: "b"})

    assert delivered == 2
    assert bot.sent == [(1, "a"), (2, "b")]


async def test_blocked_user_is_deactivated_not_deleted(storage):
    await storage.ensure_user(1)
    await storage.set_subscribed(1, True)
    await storage.toggle_zone(1, 26)
    bot = FakeBot(fail_with={1: method_error(TelegramForbiddenError, "bot was blocked")})

    delivered = await Broadcaster(bot, storage, rate=10_000).fan_out({1: "hi"})

    assert delivered == 0
    assert await storage.all_active_ids() == []
    # The row survives, so /start brings them back with their filter intact.
    assert await storage.zone_filter(1) == {26}
    assert (await storage.stats())["total"] == 1


async def test_transient_failure_does_not_unsubscribe(storage):
    await storage.ensure_user(1)
    await storage.set_subscribed(1, True)
    bot = FakeBot(fail_with={1: TimeoutError("network hiccup")})

    delivered = await Broadcaster(bot, storage, rate=10_000).fan_out({1: "hi"})

    assert delivered == 1  # counted as still-ours, just not delivered now
    assert await storage.all_active_ids() == [1]
    assert await storage.is_subscribed(1) is True


async def test_flood_control_retries_after_sleeping(storage, monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("tzbot.tracker.asyncio.sleep", fake_sleep)
    await storage.ensure_user(1)
    retry = TelegramRetryAfter(method=object(), message="slow down", retry_after=7)
    bot = FakeBot(fail_with={1: retry})

    delivered = await Broadcaster(bot, storage, rate=10_000).fan_out({1: "hi"})

    assert delivered == 1
    assert 7 in slept
    assert bot.sent == [(1, "hi")]


@pytest.mark.parametrize("rate", [0, -1, -0.5])
def test_rate_must_be_positive(rate):
    """A zero rate used to be a ZeroDivisionError at the first send."""
    with pytest.raises(ValueError, match="positive"):
        Broadcaster(FakeBot(), storage=None, rate=rate)
