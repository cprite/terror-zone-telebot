"""Subscriber state, zone filters, adverts."""

from __future__ import annotations

import datetime as dt

from tzbot.storage import Subscriber


async def test_ensure_user_is_idempotent(storage):
    await storage.ensure_user(1, "ru")
    await storage.ensure_user(1, "en")
    assert await storage.get_language(1) == "ru"
    assert (await storage.stats())["total"] == 1


async def test_subscription_round_trip(storage):
    await storage.ensure_user(7)
    assert await storage.is_subscribed(7) is False

    await storage.set_subscribed(7, True)
    assert await storage.is_subscribed(7) is True
    assert [s.user_id for s in await storage.subscribers()] == [7]

    await storage.set_subscribed(7, False)
    assert await storage.subscribers() == []


async def test_zone_filter_toggles(storage):
    await storage.ensure_user(3)
    assert await storage.toggle_zone(3, 26) is True
    assert await storage.toggle_zone(3, 10) is True
    assert await storage.zone_filter(3) == {10, 26}

    assert await storage.toggle_zone(3, 26) is False
    assert await storage.zone_filter(3) == {10}


async def test_subscribers_carry_their_filter(storage):
    await storage.ensure_user(1, "de")
    await storage.set_subscribed(1, True)
    await storage.toggle_zone(1, 5)

    await storage.ensure_user(2)
    await storage.set_subscribed(2, True)

    by_id = {s.user_id: s for s in await storage.subscribers()}
    assert by_id[1].zone_ids == {5}
    assert by_id[1].language == "de"
    assert by_id[2].zone_ids == frozenset()


def test_empty_filter_means_every_zone():
    everything = Subscriber(1, "en", frozenset())
    picky = Subscriber(2, "en", frozenset({5}))

    assert everything.wants(26) and everything.wants(None)
    assert picky.wants(5)
    assert not picky.wants(26)
    # An unrecognised zone must not be forced on someone with a filter.
    assert not picky.wants(None)


async def test_deactivate_keeps_the_row_and_the_filter(storage):
    """A user who blocks the bot may come back; their choices are still theirs."""
    await storage.ensure_user(9)
    await storage.set_subscribed(9, True)
    await storage.toggle_zone(9, 12)

    await storage.deactivate(9)
    assert await storage.subscribers() == []
    assert await storage.all_active_ids() == []
    assert await storage.zone_filter(9) == {12}

    await storage.ensure_user(9)
    assert await storage.all_active_ids() == [9]


async def test_advert_expires(storage):
    await storage.set_advert("buy runes", days=1)
    assert await storage.advert() == "buy runes"

    past = (dt.datetime.now(dt.UTC) - dt.timedelta(minutes=1)).isoformat()
    await storage.db.execute("UPDATE advert SET ends_at = ?", (past,))
    await storage.db.commit()

    assert await storage.advert() is None
    # Expiry clears the row rather than re-checking it forever.
    async with storage.db.execute("SELECT count(*) AS n FROM advert") as cursor:
        assert (await cursor.fetchone())["n"] == 0


async def test_maintenance_flag(storage):
    assert await storage.maintenance() is False
    await storage.set_maintenance(True)
    assert await storage.maintenance() is True


async def test_stats(storage):
    for user_id in (1, 2, 3):
        await storage.ensure_user(user_id)
    await storage.set_subscribed(1, True)
    await storage.set_subscribed(2, True)
    await storage.toggle_zone(1, 4)
    await storage.deactivate(3)

    assert await storage.stats() == {
        "total": 3,
        "active": 2,
        "subscribed": 2,
        "filtered": 1,
    }
