from __future__ import annotations

from datetime import datetime, timezone

from database.database import Database


class GuildRepository:
    def __init__(self, db: Database):
        self.db = db

    async def ensure_guild(self, guild_id: int, name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.conn.execute(
            """
            INSERT INTO guilds (guild_id, name, joined_at)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET name = excluded.name
            """,
            (str(guild_id), name, now),
        )
        await self.db.conn.commit()

    async def get_settings(self, guild_id: int) -> dict | None:
        cur = await self.db.conn.execute(
            "SELECT * FROM guilds WHERE guild_id = ?", (str(guild_id),)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def set_timezone(self, guild_id: int, tz_name: str) -> None:
        await self.db.conn.execute(
            "UPDATE guilds SET timezone = ? WHERE guild_id = ?", (tz_name, str(guild_id))
        )
        await self.db.conn.commit()

    async def set_tracking_flag(self, guild_id: int, column: str, enabled: bool) -> None:
        if column not in {"track_presence", "track_messages", "track_voice", "exclude_solo_vc"}:
            raise ValueError(f"invalid settings column: {column}")
        await self.db.conn.execute(
            f"UPDATE guilds SET {column} = ? WHERE guild_id = ?",
            (1 if enabled else 0, str(guild_id)),
        )
        await self.db.conn.commit()

    async def ensure_member(self, guild_id: int, user_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.conn.execute(
            """
            INSERT INTO guild_members (guild_id, user_id, tracking_since)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO NOTHING
            """,
            (str(guild_id), str(user_id), now),
        )
        await self.db.conn.commit()

    async def tracking_since(self, guild_id: int, user_id: int) -> str | None:
        cur = await self.db.conn.execute(
            "SELECT tracking_since FROM guild_members WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return row["tracking_since"] if row else None

    async def is_opted_out(self, guild_id: int, user_id: int) -> bool:
        cur = await self.db.conn.execute(
            "SELECT opted_out FROM guild_members WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return bool(row["opted_out"]) if row else False

    async def set_opt_out(self, guild_id: int, user_id: int, opted_out: bool) -> None:
        await self.ensure_member(guild_id, user_id)
        await self.db.conn.execute(
            "UPDATE guild_members SET opted_out = ? WHERE guild_id = ? AND user_id = ?",
            (1 if opted_out else 0, str(guild_id), str(user_id)),
        )
        await self.db.conn.commit()

    async def delete_all_user_data(self, guild_id: int, user_id: int) -> None:
        """Used by /privacy delete-my-data. Wipes every table scoped to this member."""
        gid, uid = str(guild_id), str(user_id)
        tables_with_user = [
            "message_daily", "message_hourly", "user_streaks", "voice_sessions",
            "voice_daily", "reaction_stats", "game_stats", "music_stats",
            "presence_sessions", "guild_members",
        ]
        for table in tables_with_user:
            await self.db.conn.execute(
                f"DELETE FROM {table} WHERE guild_id = ? AND user_id = ?", (gid, uid)
            )
        await self.db.conn.execute(
            "DELETE FROM voice_pairs WHERE guild_id = ? AND (user_a = ? OR user_b = ?)",
            (gid, uid, uid),
        )
        await self.db.conn.commit()


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    async def upsert(self, user_id: int, username: str, avatar_key: str | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.conn.execute(
            """
            INSERT INTO users (user_id, username, avatar_key, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                avatar_key = excluded.avatar_key
            """,
            (str(user_id), username, avatar_key, now),
        )
        await self.db.conn.commit()
