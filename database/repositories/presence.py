from __future__ import annotations

from database.database import Database


class PresenceRepository:
    """Handles the open/close session pattern for game & music presence.

    Discord presence updates are event-driven, not a continuous feed:
    we get "you started playing X" and "you stopped" (or switched to Y),
    never a duration. So we open a session row when an activity starts
    and close it (turning it into an estimated_seconds delta) when it
    ends, gets replaced, or the member goes offline.
    """

    def __init__(self, db: Database):
        self.db = db

    async def open_session(self, guild_id: int, user_id: int, kind: str, name: str,
                            started_at: str) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO presence_sessions (guild_id, user_id, kind, name, started_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, kind) DO UPDATE SET
                name = excluded.name, started_at = excluded.started_at
            """,
            (str(guild_id), str(user_id), kind, name, started_at),
        )
        await self.db.conn.commit()

    async def get_open_session(self, guild_id: int, user_id: int, kind: str) -> dict | None:
        cur = await self.db.conn.execute(
            "SELECT name, started_at FROM presence_sessions "
            "WHERE guild_id = ? AND user_id = ? AND kind = ?",
            (str(guild_id), str(user_id), kind),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def close_session(self, guild_id: int, user_id: int, kind: str) -> None:
        await self.db.conn.execute(
            "DELETE FROM presence_sessions WHERE guild_id = ? AND user_id = ? AND kind = ?",
            (str(guild_id), str(user_id), kind),
        )
        await self.db.conn.commit()

    async def record_game_time(self, guild_id: int, user_id: int, game_name: str,
                                seconds: int, timestamp: str) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO game_stats
                (guild_id, user_id, game_name, estimated_seconds, sessions_observed,
                 first_seen, last_seen)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(guild_id, user_id, game_name) DO UPDATE SET
                estimated_seconds = estimated_seconds + excluded.estimated_seconds,
                sessions_observed = sessions_observed + 1,
                last_seen = excluded.last_seen
            """,
            (str(guild_id), str(user_id), game_name, seconds, timestamp, timestamp),
        )
        await self.db.conn.commit()

    async def record_music_time(self, guild_id: int, user_id: int, artist: str, track: str,
                                 seconds: int, timestamp: str) -> None:
        await self.db.conn.execute(
            """
            INSERT INTO music_stats
                (guild_id, user_id, artist, track, observed_count, estimated_seconds, last_seen)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(guild_id, user_id, artist, track) DO UPDATE SET
                observed_count = observed_count + 1,
                estimated_seconds = estimated_seconds + excluded.estimated_seconds,
                last_seen = excluded.last_seen
            """,
            (str(guild_id), str(user_id), artist, track, seconds, timestamp),
        )
        await self.db.conn.commit()

    async def top_games(self, guild_id: int, user_id: int, limit: int = 5) -> list[dict]:
        cur = await self.db.conn.execute(
            "SELECT game_name, estimated_seconds, sessions_observed FROM game_stats "
            "WHERE guild_id = ? AND user_id = ? ORDER BY estimated_seconds DESC LIMIT ?",
            (str(guild_id), str(user_id), limit),
        )
        return [dict(r) for r in await cur.fetchall()]

    async def top_artist(self, guild_id: int, user_id: int) -> dict | None:
        cur = await self.db.conn.execute(
            "SELECT artist, SUM(observed_count) as total FROM music_stats "
            "WHERE guild_id = ? AND user_id = ? GROUP BY artist "
            "ORDER BY total DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def top_track(self, guild_id: int, user_id: int) -> dict | None:
        cur = await self.db.conn.execute(
            "SELECT artist, track, observed_count FROM music_stats "
            "WHERE guild_id = ? AND user_id = ? ORDER BY observed_count DESC LIMIT 1",
            (str(guild_id), str(user_id)),
        )
        row = await cur.fetchone()
        return dict(row) if row else None
