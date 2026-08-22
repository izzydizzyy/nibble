"""
Thin async wrapper around aiosqlite. Two tables:

guild_config    -- one row per guild, holds the default log channel + toggle master switch
event_channels  -- optional per-event channel override (falls back to guild_config.log_channel)
"""

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id      INTEGER PRIMARY KEY,
    log_channel   INTEGER,
    enabled       INTEGER NOT NULL DEFAULT 1,
    ignored_users TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS event_toggles (
    guild_id   INTEGER NOT NULL,
    event_key  TEXT NOT NULL,
    enabled    INTEGER NOT NULL DEFAULT 1,
    channel_id INTEGER,
    PRIMARY KEY (guild_id, event_key)
);

CREATE TABLE IF NOT EXISTS votes (
    user_id    INTEGER PRIMARY KEY,
    last_vote  TEXT
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def get_guild_config(self, guild_id: int) -> dict:
        cur = await self._conn.execute(
            "SELECT log_channel, enabled, ignored_users FROM guild_config WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cur.fetchone()
        if row is None:
            await self._conn.execute(
                "INSERT INTO guild_config (guild_id) VALUES (?)", (guild_id,)
            )
            await self._conn.commit()
            return {"log_channel": None, "enabled": True, "ignored_users": ""}
        return {"log_channel": row[0], "enabled": bool(row[1]), "ignored_users": row[2]}

    async def set_log_channel(self, guild_id: int, channel_id: int | None):
        await self.get_guild_config(guild_id)  # ensure row exists
        await self._conn.execute(
            "UPDATE guild_config SET log_channel = ? WHERE guild_id = ?",
            (channel_id, guild_id),
        )
        await self._conn.commit()

    async def set_enabled(self, guild_id: int, enabled: bool):
        await self.get_guild_config(guild_id)
        await self._conn.execute(
            "UPDATE guild_config SET enabled = ? WHERE guild_id = ?",
            (int(enabled), guild_id),
        )
        await self._conn.commit()

    async def get_event_toggle(self, guild_id: int, event_key: str) -> dict:
        cur = await self._conn.execute(
            "SELECT enabled, channel_id FROM event_toggles WHERE guild_id = ? AND event_key = ?",
            (guild_id, event_key),
        )
        row = await cur.fetchone()
        if row is None:
            return {"enabled": True, "channel_id": None}
        return {"enabled": bool(row[0]), "channel_id": row[1]}

    async def set_event_toggle(self, guild_id: int, event_key: str, enabled: bool):
        await self._conn.execute(
            """
            INSERT INTO event_toggles (guild_id, event_key, enabled)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, event_key) DO UPDATE SET enabled = excluded.enabled
            """,
            (guild_id, event_key, int(enabled)),
        )
        await self._conn.commit()

    async def set_event_channel(self, guild_id: int, event_key: str, channel_id: int | None):
        await self._conn.execute(
            """
            INSERT INTO event_toggles (guild_id, event_key, channel_id, enabled)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, event_key) DO UPDATE SET channel_id = excluded.channel_id
            """,
            (guild_id, event_key, channel_id),
        )
        await self._conn.commit()

    async def resolve_log_channel(self, guild_id: int, event_key: str) -> int | None:
        """Per-event override wins, otherwise fall back to the guild default."""
        toggle = await self.get_event_toggle(guild_id, event_key)
        if not toggle["enabled"]:
            return None
        if toggle["channel_id"]:
            return toggle["channel_id"]
        cfg = await self.get_guild_config(guild_id)
        if not cfg["enabled"]:
            return None
        return cfg["log_channel"]

    async def record_vote(self, user_id: int, timestamp: str):
        await self._conn.execute(
            """
            INSERT INTO votes (user_id, last_vote) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_vote = excluded.last_vote
            """,
            (user_id, timestamp),
        )
        await self._conn.commit()
