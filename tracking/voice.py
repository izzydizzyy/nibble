from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import discord

from database.repositories.voice import VoiceRepository
from utils.time import get_zone, now_utc

log = logging.getLogger("replay.tracking")


@dataclass
class OpenSession:
    channel_id: int
    started_at: datetime
    was_solo: bool
    other_member_ids: set[int]


class VoiceTracker:
    """Tracks join/leave/move/disconnect via a per-member open-session map.

    Solo detection is a snapshot taken when the session opens (and
    re-taken on channel switch) rather than a continuous re-evaluation —
    if someone joins the channel a minute into a "solo" session, that
    session is still recorded as solo. This is a deliberate simplification;
    a fully accurate version would need to split sessions on every
    membership change in the channel, which isn't worth the complexity
    for V1. Noted here instead of pretending it's exact.
    """

    def __init__(self, repo: VoiceRepository, get_guild_settings):
        self.repo = repo
        self._get_settings = get_guild_settings
        self._open: dict[tuple[int, int], OpenSession] = {}

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return

        settings = await self._get_settings(member.guild.id)
        if not settings.get("track_voice", True):
            return

        key = (member.guild.id, member.id)

        if before.channel is None and after.channel is not None:
            await self._open_session(member.guild.id, member.id, after.channel)
        elif before.channel is not None and after.channel is None:
            await self._close_session(member.guild.id, member.id, settings)
        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            await self._close_session(member.guild.id, member.id, settings)
            await self._open_session(member.guild.id, member.id, after.channel)
        # mute/deafen-only changes: no-op, session continues

    async def _open_session(self, guild_id: int, user_id: int, channel: discord.VoiceChannel) -> None:
        others = {m.id for m in channel.members if not m.bot and m.id != user_id}
        self._open[(guild_id, user_id)] = OpenSession(
            channel_id=channel.id,
            started_at=now_utc(),
            was_solo=len(others) == 0,
            other_member_ids=others,
        )

    async def _close_session(self, guild_id: int, user_id: int, settings: dict) -> None:
        key = (guild_id, user_id)
        session = self._open.pop(key, None)
        if session is None:
            return

        ended_at = now_utc()
        duration = int((ended_at - session.started_at).total_seconds())
        if duration <= 0:
            return

        exclude_solo = bool(settings.get("exclude_solo_vc", True))
        if session.was_solo and exclude_solo:
            return

        tz = get_zone(settings.get("timezone", "UTC"))
        daily_buckets = self._split_across_days(session.started_at, ended_at, tz)

        await self.repo.record_session(
            guild_id, user_id, session.channel_id,
            session.started_at.isoformat(), ended_at.isoformat(), duration,
            session.was_solo, daily_buckets,
        )

        seconds_each = duration
        for other_id in session.other_member_ids:
            await self.repo.record_pair_time(guild_id, user_id, other_id, seconds_each, ended_at.isoformat())

    @staticmethod
    def _split_across_days(start: datetime, end: datetime, tz) -> dict[str, int]:
        buckets: dict[str, int] = {}
        cursor = start.astimezone(tz)
        end_local = end.astimezone(tz)
        while cursor.date() < end_local.date():
            next_midnight = (cursor + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            buckets[cursor.date().isoformat()] = int((next_midnight - cursor).total_seconds())
            cursor = next_midnight
        buckets[cursor.date().isoformat()] = buckets.get(cursor.date().isoformat(), 0) + int(
            (end_local - cursor).total_seconds()
        )
        return buckets

    async def flush_all_open(self, get_guild_settings) -> None:
        """Called on shutdown so nobody's current VC time is lost."""
        for (guild_id, user_id) in list(self._open.keys()):
            settings = await get_guild_settings(guild_id)
            await self._close_session(guild_id, user_id, settings)
