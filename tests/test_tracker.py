"""Rotation detection and fan-out."""

from __future__ import annotations

import datetime as dt

import pytest

from tzbot.providers.base import ProviderError, Snapshot
from tzbot.tracker import ALERT_ICON, Tracker

DURANCE = "Durance of Hate"
TRAVINCAL = "Travincal"
TRISTRAM = "Tristram"

DURANCE_ID = 26
TRAVINCAL_ID = 25


class FakeProvider:
    name = "fake"

    def __init__(self, *snapshots: Snapshot | Exception) -> None:
        self._queue = list(snapshots)
        self.calls = 0

    async def fetch(self) -> Snapshot:
        self.calls += 1
        item = self._queue.pop(0) if len(self._queue) > 1 else self._queue[0]
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self) -> None:
        return None


class FakeBroadcaster:
    def __init__(self) -> None:
        self.batches: list[dict[int, str]] = []

    async def fan_out(self, messages: dict[int, str]) -> int:
        self.batches.append(messages)
        return len(messages)

    @property
    def recipients(self) -> set[int]:
        return {user for batch in self.batches for user in batch}


def snap(current: str, nxt: str) -> Snapshot:
    return Snapshot(current_raw=current, next_raw=nxt)


def at(hour: int, minute: int) -> dt.datetime:
    return dt.datetime(2026, 9, 9, hour, minute, tzinfo=dt.UTC)


@pytest.fixture
def broadcaster():
    return FakeBroadcaster()


def build(provider, storage, broadcaster) -> Tracker:
    return Tracker(provider, storage, broadcaster, poll_interval=60, prealert_minute=45)


async def subscribe(storage, user_id: int, *zone_ids: int, language: str = "en") -> None:
    await storage.ensure_user(user_id, language)
    await storage.set_subscribed(user_id, True)
    for zone_id in zone_ids:
        await storage.toggle_zone(user_id, zone_id)


async def test_first_tick_only_primes(storage, broadcaster):
    """Starting the bot must not tell everyone the zone "changed"."""
    await subscribe(storage, 1)
    tracker = build(FakeProvider(snap(TRAVINCAL, DURANCE)), storage, broadcaster)

    await tracker.tick(at(12, 10))

    assert tracker.snapshot.current_raw == TRAVINCAL
    assert broadcaster.batches == []


async def test_rotation_is_announced_once(storage, broadcaster):
    await subscribe(storage, 1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))
    await tracker.tick(at(13, 2))  # nothing changed since

    assert len(broadcaster.batches) == 1
    assert DURANCE in broadcaster.batches[0][1]


async def test_zone_filter_is_respected(storage, broadcaster):
    await subscribe(storage, 1, DURANCE_ID)     # wants only Durance
    await subscribe(storage, 2, TRAVINCAL_ID)   # wants only Travincal
    await subscribe(storage, 3)                 # wants everything
    await storage.ensure_user(4)                # never subscribed

    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    assert broadcaster.recipients == {1, 3}


async def test_messages_use_each_subscribers_language(storage, broadcaster):
    await subscribe(storage, 1, language="ru")
    await subscribe(storage, 2, language="de")
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    batch = broadcaster.batches[0]
    assert "Воины Санктуария" in batch[1]
    assert "Krieger des Heiligtums" in batch[2]


async def test_prealert_fires_once_per_hour(storage, broadcaster):
    await subscribe(storage, 1)
    tracker = build(FakeProvider(snap(TRAVINCAL, DURANCE)), storage, broadcaster)

    await tracker.tick(at(12, 10))   # prime
    await tracker.tick(at(12, 44))   # too early
    assert broadcaster.batches == []

    await tracker.tick(at(12, 46))   # inside the window
    await tracker.tick(at(12, 59))   # same hour, must not repeat
    assert len(broadcaster.batches) == 1
    assert DURANCE in broadcaster.batches[0][1]

    await tracker.tick(at(13, 50))   # next hour, fires again
    assert len(broadcaster.batches) == 2


async def test_prealert_targets_the_next_zone_filter(storage, broadcaster):
    """The heads-up goes to people who care about what is *coming*."""
    await subscribe(storage, 1, DURANCE_ID)
    await subscribe(storage, 2, TRAVINCAL_ID)
    tracker = build(FakeProvider(snap(TRAVINCAL, DURANCE)), storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(12, 46))

    assert broadcaster.recipients == {1}


async def test_maintenance_silences_broadcasts(storage, broadcaster):
    await subscribe(storage, 1)
    await storage.set_maintenance(True)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    assert broadcaster.batches == []


async def test_advert_is_appended(storage, broadcaster):
    await subscribe(storage, 1)
    await storage.set_advert("buy runes", days=1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    assert broadcaster.batches[0][1].endswith("buy runes")


async def test_provider_outage_keeps_the_last_snapshot(storage, broadcaster):
    await subscribe(storage, 1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), ProviderError("boom"))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(12, 11))

    assert tracker.snapshot.current_raw == TRAVINCAL
    assert broadcaster.batches == []


async def test_unrecognised_zone_is_still_relayed(storage, broadcaster):
    """An upstream rename must not silence the bot for unfiltered users."""
    await subscribe(storage, 1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap("Brand New Zone", TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    assert "Brand New Zone" in broadcaster.batches[0][1]


async def test_zone_name_is_the_first_line(storage, broadcaster):
    """Telegram's notification preview cuts everything after the opening lines.

    The zone used to sit on line five, under the flavour text, so a push
    notification showed the greeting and hid the one fact that matters.
    """
    await subscribe(storage, 1, language="ru")
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))          # rotation
    await tracker.tick(at(13, 46))         # prealert

    icons = set(ALERT_ICON.values())
    for batch in broadcaster.batches:
        first, second, *_ = batch[1].splitlines()
        icon, _, zone = first.partition(" ")
        assert icon in icons, f"line 1 must open with an alert icon, got {first!r}"
        assert zone in (DURANCE, TRISTRAM), f"line 1 zone was {zone!r}"
        assert second.strip(), "line 2 must carry the status, not be blank"


async def test_the_two_alerts_use_different_icons(storage, broadcaster):
    """At a glance the icon says "starts soon" or "live now"."""
    await subscribe(storage, 1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))          # rotation
    await tracker.tick(at(13, 46))         # prealert

    rotation, prealert = (b[1].split(" ", 1)[0] for b in broadcaster.batches)
    assert rotation == ALERT_ICON["rotation"]
    assert prealert == ALERT_ICON["prealert"]
    assert rotation != prealert


async def test_advert_does_not_push_the_zone_down(storage, broadcaster):
    await subscribe(storage, 1)
    await storage.set_advert("buy runes", days=1)
    provider = FakeProvider(snap(TRAVINCAL, DURANCE), snap(DURANCE, TRISTRAM))
    tracker = build(provider, storage, broadcaster)

    await tracker.tick(at(12, 10))
    await tracker.tick(at(13, 1))

    body = broadcaster.batches[0][1]
    assert body.splitlines()[0] == f"{ALERT_ICON['rotation']} {DURANCE}"
    assert body.endswith("buy runes")
