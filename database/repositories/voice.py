from __future__ import annotations

from database.database import Database


def _pair_key(a: int, b: int) -> tuple[str, str]:
    sa, sb = str(a), str(b)
    return (sa, sb) if sa < sb else (sb, sa)


class VoiceRepository:
    def __init__(self, db: Database):
        self.db = db

    async def record_session(
        self,
        guild_id: int,
        user_id: int,
        channel_id: int,
        started_at: str,
        ended_at: str,
        duration_seconds: int,
        was_solo: bool,
        daily_buckets: dict[str, int],
    ) -> None:
        """daily_buckets: local_date -> seconds, for sessions spanning midnight."""
        conn = self.db.conn
        await conn.execute(
            """
            INSERT INTO voice_sessions
                (guild_id, user_id, channel_id, started_at, ended_at, duration_seconds, was_solo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(guild_id), str(user_id), str(channel_id), started_at, ended_at,
             duration_seconds, 1 if was_solo else 0),
        )
        for local_date, seconds in daily_buckets.items():
            await conn.execute(
                """
                INSERT INTO voice_daily (guild_id, user_id, date, seconds)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id, date) DO UPDATE SET seconds = seconds + excluded.seconds
                """,
                (str(guild_id), str(user_id), local_date, seconds),
            )
        await conn.commit()

    async def record_pair_time(self, guild_id: int, user_id_a: int, user_id_b: int,
                                seconds: int, timestamp: str) -> None:
        a, b = _pair_key(user_id_a, user_id_b)
        await self.db.conn.execute(
            """
            INSERT INTO voice_pairs (guild_id, user_a, user_b, seconds_together, last_together)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_a, user_b) DO UPDATE SET
                seconds_together = seconds_together + excluded.seconds_together,
                last_together = excluded.last_together
            """,
            (str(guild_id), a, b, seconds, timestamp),
        )
        await self.db.conn.commit()

    async def total_seconds(self, guild_id: int, user_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(seconds), 0) as total FROM voice_daily "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return (await cur.fetchone())["total"]

    async def seconds_since(self, guild_id: int, user_id: int, since_date: str) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(seconds), 0) as total FROM voice_daily "
            "WHERE guild_id = ? AND user_id = ? AND date >= ?",
            (str(guild_id), str(user_id), since_date),
        )
        return (await cur.fetchone())["total"]

    async def longest_session(self, guild_id: int, user_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(MAX(duration_seconds), 0) as longest FROM voice_sessions "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return (await cur.fetchone())["longest"]

    async def session_count(self, guild_id: int, user_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COUNT(*) as n FROM voice_sessions WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return (await cur.fetchone())["n"]

    async def favorite_channel(self, guild_id: int, user_id: int) -> str | None:
        cur = await self.db.conn.execute(
            "SELECT channel_id, SUM(duration_seconds) as total FROM voice_sessions "
            "WHERE guild_id = ? AND user_id = ? GROUP BY channel_id "
            "ORDER BY total DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return row["channel_id"] if row else None

    async def top_pair(self, guild_id: int, user_id: int, limit: int = 1) -> list[dict]:
        cur = await self.db.conn.execute(
            "SELECT user_a, user_b, seconds_together FROM voice_pairs "
            "WHERE guild_id = ? AND (user_a = ? OR user_b = ?) "
            "ORDER BY seconds_together DESC LIMIT ?",
            (str(guild_id), str(user_id), str(user_id), limit),
        )
        rows = await cur.fetchall()
        results = []
        for r in rows:
            other = r["user_b"] if r["user_a"] == str(user_id) else r["user_a"]
            results.append({"user_id": int(other), "seconds_together": r["seconds_together"]})
        return results

    async def pair_seconds(self, guild_id: int, user_id_a: int, user_id_b: int) -> int:
        a, b = _pair_key(user_id_a, user_id_b)
        cur = await self.db.conn.execute(
            "SELECT seconds_together FROM voice_pairs WHERE guild_id = ? AND user_a = ? AND user_b = ?",
            (str(guild_id), a, b),
        )
        row = await cur.fetchone()
        return row["seconds_together"] if row else 0

    async def leaderboard(self, guild_id: int, since_date: str | None, limit: int = 10) -> list[dict]:
        conn = self.db.conn
        if since_date:
            cur = await conn.execute(
                "SELECT user_id, SUM(seconds) as total FROM voice_daily "
                "WHERE guild_id = ? AND date >= ? GROUP BY user_id "
                "ORDER BY total DESC LIMIT ?",
                (str(guild_id), since_date, limit),
            )
        else:
            cur = await conn.execute(
                "SELECT user_id, SUM(seconds) as total FROM voice_daily "
                "WHERE guild_id = ? GROUP BY user_id ORDER BY total DESC LIMIT ?",
                (str(guild_id), limit),
            )
        rows = await cur.fetchall()
        return [{"user_id": int(r["user_id"]), "value": r["total"]} for r in rows]

    async def guild_total_seconds(self, guild_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(seconds), 0) as total FROM voice_daily WHERE guild_id = ?",
            (str(guild_id),),
        )
        return (await cur.fetchone())["total"]
