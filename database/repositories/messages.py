from __future__ import annotations

from datetime import date, timedelta

from database.database import Database


class MessageRepository:
    def __init__(self, db: Database):
        self.db = db

    async def record_batch(self, events: list[tuple[int, int, int, str, int]]) -> None:
        """events: (guild_id, user_id, channel_id, local_date, hour) tuples.
        Called by the tracking queue's flush worker, not per-message.
        """
        if not events:
            return
        conn = self.db.conn
        for guild_id, user_id, channel_id, local_date, hour in events:
            await conn.execute(
                """
                INSERT INTO message_daily (guild_id, user_id, channel_id, date, count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(guild_id, user_id, channel_id, date)
                DO UPDATE SET count = count + 1
                """,
                (str(guild_id), str(user_id), str(channel_id), local_date),
            )
            await conn.execute(
                """
                INSERT INTO message_hourly (guild_id, user_id, hour, count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(guild_id, user_id, hour) DO UPDATE SET count = count + 1
                """,
                (str(guild_id), str(user_id), hour),
            )
        await conn.commit()

    async def bump_streak(self, guild_id: int, user_id: int, local_date: str) -> None:
        conn = self.db.conn
        cur = await conn.execute(
            "SELECT current_streak, longest_streak, last_active_date FROM user_streaks "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        today = date.fromisoformat(local_date)

        if row is None:
            await conn.execute(
                "INSERT INTO user_streaks (guild_id, user_id, current_streak, longest_streak, "
                "last_active_date) VALUES (?, ?, 1, 1, ?)",
                (str(guild_id), str(user_id), local_date),
            )
            await conn.commit()
            return

        last_active = row["last_active_date"]
        if last_active == local_date:
            return  # already counted today

        current, longest = row["current_streak"], row["longest_streak"]
        if last_active and date.fromisoformat(last_active) == today - timedelta(days=1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)

        await conn.execute(
            "UPDATE user_streaks SET current_streak = ?, longest_streak = ?, "
            "last_active_date = ? WHERE guild_id = ? AND user_id = ?",
            (current, longest, local_date, str(guild_id), str(user_id)),
        )
        await conn.commit()

    async def totals(self, guild_id: int, user_id: int) -> dict:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM message_daily "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        total = (await cur.fetchone())["total"]
        return {"total": total}

    async def totals_since(self, guild_id: int, user_id: int, since_date: str) -> int:
        cur = await self.db.conn.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM message_daily "
            "WHERE guild_id = ? AND user_id = ? AND date >= ?",
            (str(guild_id), str(user_id), since_date),
        )
        return (await cur.fetchone())["total"]

    async def top_channel(self, guild_id: int, user_id: int) -> tuple[str, int] | None:
        cur = await self.db.conn.execute(
            "SELECT channel_id, SUM(count) as total FROM message_daily "
            "WHERE guild_id = ? AND user_id = ? GROUP BY channel_id "
            "ORDER BY total DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return (row["channel_id"], row["total"]) if row else None

    async def favorite_hour(self, guild_id: int, user_id: int) -> int | None:
        cur = await self.db.conn.execute(
            "SELECT hour FROM message_hourly WHERE guild_id = ? AND user_id = ? "
            "ORDER BY count DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return row["hour"] if row else None

    async def hourly_distribution(self, guild_id: int, user_id: int) -> dict[int, int]:
        cur = await self.db.conn.execute(
            "SELECT hour, count FROM message_hourly WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        rows = await cur.fetchall()
        return {r["hour"]: r["count"] for r in rows}

    async def active_hours_set(self, guild_id: int, user_id: int) -> set[int]:
        cur = await self.db.conn.execute(
            "SELECT hour FROM message_hourly WHERE guild_id = ? AND user_id = ? AND count > 0",
            (str(guild_id), str(user_id)),
        )
        return {r["hour"] for r in await cur.fetchall()}

    async def channels_used(self, guild_id: int, user_id: int) -> set[int]:
        cur = await self.db.conn.execute(
            "SELECT DISTINCT channel_id FROM message_daily WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return {int(r["channel_id"]) for r in await cur.fetchall()}

    async def active_dates_set(self, guild_id: int, user_id: int) -> set[str]:
        cur = await self.db.conn.execute(
            "SELECT DISTINCT date FROM message_daily WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return {r["date"] for r in await cur.fetchall()}

    async def active_days(self, guild_id: int, user_id: int) -> int:
        cur = await self.db.conn.execute(
            "SELECT COUNT(DISTINCT date) as days FROM message_daily "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        return (await cur.fetchone())["days"]

    async def streak(self, guild_id: int, user_id: int) -> dict:
        cur = await self.db.conn.execute(
            "SELECT current_streak, longest_streak FROM user_streaks "
            "WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        if not row:
            return {"current": 0, "longest": 0}
        return {"current": row["current_streak"], "longest": row["longest_streak"]}

    async def leaderboard(self, guild_id: int, since_date: str | None, limit: int = 10) -> list[dict]:
        conn = self.db.conn
        if since_date:
            cur = await conn.execute(
                "SELECT user_id, SUM(count) as total FROM message_daily "
                "WHERE guild_id = ? AND date >= ? GROUP BY user_id "
                "ORDER BY total DESC LIMIT ?",
                (str(guild_id), since_date, limit),
            )
        else:
            cur = await conn.execute(
                "SELECT user_id, SUM(count) as total FROM message_daily "
                "WHERE guild_id = ? GROUP BY user_id ORDER BY total DESC LIMIT ?",
                (str(guild_id), limit),
            )
        rows = await cur.fetchall()
        return [{"user_id": int(r["user_id"]), "value": r["total"]} for r in rows]

    async def guild_totals(self, guild_id: int) -> dict:
        conn = self.db.conn
        cur = await conn.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM message_daily WHERE guild_id = ?",
            (str(guild_id),),
        )
        total = (await cur.fetchone())["total"]

        cur = await conn.execute(
            "SELECT channel_id, SUM(count) as total FROM message_daily WHERE guild_id = ? "
            "GROUP BY channel_id ORDER BY total DESC LIMIT 1",
            (str(guild_id),),
        )
        top_channel_row = await cur.fetchone()

        cur = await conn.execute(
            "SELECT date, SUM(count) as total FROM message_daily WHERE guild_id = ? "
            "GROUP BY date ORDER BY total DESC LIMIT 1",
            (str(guild_id),),
        )
        busiest_day_row = await cur.fetchone()

        return {
            "total_messages": total,
            "top_channel_id": top_channel_row["channel_id"] if top_channel_row else None,
            "busiest_day": busiest_day_row["date"] if busiest_day_row else None,
        }
