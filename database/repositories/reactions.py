from __future__ import annotations

from database.database import Database


class ReactionRepository:
    def __init__(self, db: Database):
        self.db = db

    async def record(self, guild_id: int, user_id: int, emoji_key: str) -> None:
        conn = self.db.conn
        await conn.execute(
            """
            INSERT INTO reaction_stats (guild_id, user_id, emoji_key, given_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, user_id, emoji_key) DO UPDATE SET given_count = given_count + 1
            """,
            (str(guild_id), str(user_id), emoji_key),
        )
        await conn.execute(
            """
            INSERT INTO emoji_stats (guild_id, emoji_key, total_count)
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id, emoji_key) DO UPDATE SET total_count = total_count + 1
            """,
            (str(guild_id), emoji_key),
        )
        await conn.commit()

    async def top_emoji(self, guild_id: int, user_id: int) -> tuple[str, int] | None:
        cur = await self.db.conn.execute(
            "SELECT emoji_key, given_count FROM reaction_stats "
            "WHERE guild_id = ? AND user_id = ? ORDER BY given_count DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return (row["emoji_key"], row["given_count"]) if row else None

    async def total_given(self, guild_id: int, user_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(given_count), 0) as total FROM reaction_stats "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return (await cur.fetchone())["total"]

    async def guild_top_emoji(self, guild_id: int) -> tuple[str, int] | None:
        cur = await self.db.conn.execute(
            "SELECT emoji_key, total_count FROM emoji_stats WHERE guild_id = ? "
            "ORDER BY total_count DESC LIMIT 1",
            (str(guild_id),),
        )
        row = await cur.fetchone()
        return (row["emoji_key"], row["total_count"]) if row else None
