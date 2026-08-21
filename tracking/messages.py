from __future__ import annotations

import discord

from database.repositories.messages import MessageRepository
from tracking.queue import BatchQueue
from utils.time import local_date_and_hour, now_utc


class MessageTracker:
    def __init__(self, repo: MessageRepository, get_guild_timezone):
        self.repo = repo
        self._get_tz = get_guild_timezone
        self.queue = BatchQueue(self._flush)
        self._streak_dates: dict[tuple[int, int], str] = {}

    def start(self) -> None:
        self.queue.start()

    async def stop(self) -> None:
        await self.queue.stop()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return

        tz_name = await self._get_tz(message.guild.id)
        local_date, hour = local_date_and_hour(now_utc(), tz_name)
        self.queue.push((message.guild.id, message.author.id, message.channel.id, local_date, hour))

        key = (message.guild.id, message.author.id)
        if self._streak_dates.get(key) != local_date:
            self._streak_dates[key] = local_date
            await self.repo.bump_streak(message.guild.id, message.author.id, local_date)

    async def _flush(self, batch: list[tuple[int, int, int, str, int]]) -> None:
        await self.repo.record_batch(batch)
