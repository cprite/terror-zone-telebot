"""SQLite persistence.

The original bot kept its state in a CSV read and rewritten through pandas on
every toggle, which lost writes under concurrency and could not survive a
restart of the notification loop.  Everything now lives in SQLite: subscriber
rows, per-user zone filters, the advert, and the maintenance flag.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    language    TEXT    NOT NULL DEFAULT 'en',
    subscribed  INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS zone_filters (
    user_id INTEGER NOT NULL,
    zone_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, zone_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS advert (
    id       INTEGER PRIMARY KEY CHECK (id = 1),
    text     TEXT NOT NULL,
    ends_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_broadcast ON users(subscribed, active);
"""


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


@dataclass(frozen=True)
class Subscriber:
    user_id: int
    language: str
    zone_ids: frozenset[int]

    def wants(self, zone_id: int | None) -> bool:
        """An empty filter means "every zone"."""
        if not self.zone_ids:
            return True
        return zone_id is not None and zone_id in self.zone_ids


class Storage:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._path.parent != Path(""):
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage.connect() was never awaited")
        return self._db

    # ---------------------------------------------------------------- users

    async def ensure_user(self, user_id: int, language: str = "en") -> None:
        """Register a user, or mark a returning one active again."""
        now = _now()
        await self.db.execute(
            """
            INSERT INTO users (user_id, language, created_at, updated_at)
                 VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET active = 1, updated_at = excluded.updated_at
            """,
            (user_id, language, now, now),
        )
        await self.db.commit()

    async def set_language(self, user_id: int, language: str) -> None:
        await self.db.execute(
            "UPDATE users SET language = ?, updated_at = ? WHERE user_id = ?",
            (language, _now(), user_id),
        )
        await self.db.commit()

    async def get_language(self, user_id: int) -> str:
        async with self.db.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return row["language"] if row else "en"

    async def set_subscribed(self, user_id: int, subscribed: bool) -> None:
        await self.db.execute(
            "UPDATE users SET subscribed = ?, updated_at = ? WHERE user_id = ?",
            (int(subscribed), _now(), user_id),
        )
        await self.db.commit()

    async def is_subscribed(self, user_id: int) -> bool:
        async with self.db.execute(
            "SELECT subscribed FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
        return bool(row and row["subscribed"])

    async def deactivate(self, user_id: int) -> None:
        """Called when Telegram tells us the user blocked or deleted the bot.

        The row is kept: the user may come back with /start, and their zone
        filter is still theirs.  The old code deleted the user on *any*
        exception, so a transient network error silently unsubscribed people.
        """
        await self.db.execute(
            "UPDATE users SET active = 0, subscribed = 0, updated_at = ? WHERE user_id = ?",
            (_now(), user_id),
        )
        await self.db.commit()

    # ------------------------------------------------------------ audiences

    async def subscribers(self) -> list[Subscriber]:
        """Everyone who should receive rotation notifications."""
        query = """
            SELECT u.user_id, u.language, group_concat(f.zone_id) AS zones
              FROM users AS u
         LEFT JOIN zone_filters AS f ON f.user_id = u.user_id
             WHERE u.subscribed = 1 AND u.active = 1
          GROUP BY u.user_id
        """
        async with self.db.execute(query) as cursor:
            rows = await cursor.fetchall()
        return [
            Subscriber(
                user_id=row["user_id"],
                language=row["language"],
                zone_ids=frozenset(
                    int(z) for z in (row["zones"] or "").split(",") if z
                ),
            )
            for row in rows
        ]

    async def all_active_ids(self) -> list[int]:
        """Everyone reachable, subscribed or not - used for announcements."""
        async with self.db.execute(
            "SELECT user_id FROM users WHERE active = 1"
        ) as cursor:
            return [row["user_id"] for row in await cursor.fetchall()]

    # --------------------------------------------------------- zone filters

    async def zone_filter(self, user_id: int) -> set[int]:
        async with self.db.execute(
            "SELECT zone_id FROM zone_filters WHERE user_id = ?", (user_id,)
        ) as cursor:
            return {row["zone_id"] for row in await cursor.fetchall()}

    async def toggle_zone(self, user_id: int, zone_id: int) -> bool:
        """Flip one zone in the user's filter. Returns True if now selected."""
        async with self.db.execute(
            "SELECT 1 FROM zone_filters WHERE user_id = ? AND zone_id = ?",
            (user_id, zone_id),
        ) as cursor:
            selected = await cursor.fetchone() is not None

        if selected:
            await self.db.execute(
                "DELETE FROM zone_filters WHERE user_id = ? AND zone_id = ?",
                (user_id, zone_id),
            )
        else:
            await self.db.execute(
                "INSERT INTO zone_filters (user_id, zone_id) VALUES (?, ?)",
                (user_id, zone_id),
            )
        await self.db.commit()
        return not selected

    async def clear_zone_filter(self, user_id: int) -> None:
        await self.db.execute("DELETE FROM zone_filters WHERE user_id = ?", (user_id,))
        await self.db.commit()

    # ------------------------------------------------------------- settings

    async def get_setting(self, key: str, default: str = "") -> str:
        async with self.db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
        return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await self.db.commit()

    async def maintenance(self) -> bool:
        return await self.get_setting("maintenance", "0") == "1"

    async def set_maintenance(self, enabled: bool) -> None:
        await self.set_setting("maintenance", "1" if enabled else "0")

    # --------------------------------------------------------------- advert

    async def set_advert(self, text: str, days: int) -> None:
        ends_at = dt.datetime.now(dt.UTC) + dt.timedelta(days=days)
        await self.db.execute(
            """
            INSERT INTO advert (id, text, ends_at) VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET text = excluded.text, ends_at = excluded.ends_at
            """,
            (text, ends_at.isoformat()),
        )
        await self.db.commit()

    async def advert(self) -> str | None:
        """The active advert, or None once it has expired."""
        async with self.db.execute("SELECT text, ends_at FROM advert WHERE id = 1") as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        if dt.datetime.fromisoformat(row["ends_at"]) <= dt.datetime.now(dt.UTC):
            await self.clear_advert()
            return None
        return row["text"] or None

    async def clear_advert(self) -> None:
        await self.db.execute("DELETE FROM advert WHERE id = 1")
        await self.db.commit()

    # ---------------------------------------------------------------- stats

    async def stats(self) -> dict[str, int]:
        query = """
            SELECT
                count(*)                                           AS total,
                coalesce(sum(active), 0)                           AS active,
                coalesce(sum(subscribed), 0)                       AS subscribed,
                (SELECT count(DISTINCT user_id) FROM zone_filters) AS filtered
            FROM users
        """
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        return {key: int(row[key]) for key in ("total", "active", "subscribed", "filtered")}
