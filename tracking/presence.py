from __future__ import annotations

from datetime import datetime

import discord

from database.repositories.presence import PresenceRepository
from utils.time import now_utc


def _current_game(member: discord.Member) -> str | None:
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing and activity.name:
            return activity.name
    return None


def _current_track(member: discord.Member) -> tuple[str, str] | None:
    for activity in member.activities:
        if isinstance(activity, discord.Spotify):
            return activity.artist, activity.title
    return None


class PresenceTracker:
    """Turns presence start/stop events into estimated durations.

    Discord doesn't hand us "played for 40 minutes" — only "started
    playing" and "stopped/changed". We open a session row on start and
    close it into estimated_seconds on stop, so numbers shown as
    "estimated" are exactly that: time observed between two presence
    events, not a verified total.
    """

    def __init__(self, repo: PresenceRepository):
        self.repo = repo

    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.bot or after.guild is None:
            return
        guild_id = after.guild.id
        user_id = after.id
        now_iso = now_utc().isoformat()

        await self._handle_kind(guild_id, user_id, "game", _current_game(before), _current_game(after), now_iso)

        before_track = _current_track(before)
        after_track = _current_track(after)
        before_key = f"{before_track[0]}||{before_track[1]}" if before_track else None
        after_key = f"{after_track[0]}||{after_track[1]}" if after_track else None
        await self._handle_kind(guild_id, user_id, "music", before_key, after_key, now_iso, track=after_track)

    async def _handle_kind(self, guild_id: int, user_id: int, kind: str,
                            before_name: str | None, after_name: str | None,
                            now_iso: str, track: tuple[str, str] | None = None) -> None:
        if before_name == after_name:
            return

        if before_name is not None:
            open_session = await self.repo.get_open_session(guild_id, user_id, kind)
            if open_session and open_session["name"] == before_name:
                started = datetime.fromisoformat(open_session["started_at"])
                seconds = max(0, int((datetime.fromisoformat(now_iso) - started).total_seconds()))
                if kind == "game":
                    await self.repo.record_game_time(guild_id, user_id, before_name, seconds, now_iso)
                else:
                    artist, title = before_name.split("||", 1)
                    await self.repo.record_music_time(guild_id, user_id, artist, title, seconds, now_iso)
                await self.repo.close_session(guild_id, user_id, kind)

        if after_name is not None:
            await self.repo.open_session(guild_id, user_id, kind, after_name, now_iso)
