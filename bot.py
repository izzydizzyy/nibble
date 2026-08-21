from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from config import config
from database.database import Database
from database.repositories.guilds import GuildRepository, UserRepository
from database.repositories.messages import MessageRepository
from database.repositories.presence import PresenceRepository
from database.repositories.reactions import ReactionRepository
from database.repositories.voice import VoiceRepository
from services.statistics import StatisticsService
from tracking.messages import MessageTracker
from tracking.presence import PresenceTracker
from tracking.reactions import ReactionTracker
from tracking.voice import VoiceTracker

logging.basicConfig(
    level=config.log_level,
    format="[%(name)s] %(message)s",
)
logging.getLogger("discord").setLevel(logging.WARNING)
log = logging.getLogger("replay")

INTENTS = discord.Intents.default()
INTENTS.message_content = False
INTENTS.members = True          # required for accurate member/channel occupancy checks
INTENTS.voice_states = True
INTENTS.presences = True        # privileged — must be enabled in the Dev Portal
INTENTS.guilds = True


class Replay(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, intents=INTENTS)

        self.db = Database(config.database_path)

        self.guild_repo: GuildRepository
        self.user_repo: UserRepository
        self.message_repo: MessageRepository
        self.voice_repo: VoiceRepository
        self.reaction_repo: ReactionRepository
        self.presence_repo: PresenceRepository

        self.message_tracker: MessageTracker
        self.voice_tracker: VoiceTracker
        self.reaction_tracker: ReactionTracker
        self.presence_tracker: PresenceTracker

        self.stats: StatisticsService

        self._settings_cache: dict[int, dict] = {}

    async def get_guild_settings(self, guild_id: int) -> dict:
        cached = self._settings_cache.get(guild_id)
        if cached:
            return cached
        settings = await self.guild_repo.get_settings(guild_id)
        if settings is None:
            settings = {
                "timezone": "UTC", "exclude_solo_vc": True,
                "track_presence": True, "track_messages": True, "track_voice": True,
            }
        self._settings_cache[guild_id] = settings
        return settings

    def invalidate_settings(self, guild_id: int) -> None:
        self._settings_cache.pop(guild_id, None)

    async def get_guild_timezone(self, guild_id: int) -> str:
        settings = await self.get_guild_settings(guild_id)
        return settings.get("timezone", "UTC")

    async def setup_hook(self) -> None:
        await self.db.connect()

        self.guild_repo = GuildRepository(self.db)
        self.user_repo = UserRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.voice_repo = VoiceRepository(self.db)
        self.reaction_repo = ReactionRepository(self.db)
        self.presence_repo = PresenceRepository(self.db)

        self.message_tracker = MessageTracker(self.message_repo, self.get_guild_timezone)
        self.voice_tracker = VoiceTracker(self.voice_repo, self.get_guild_settings)
        self.reaction_tracker = ReactionTracker(self.reaction_repo)
        self.presence_tracker = PresenceTracker(self.presence_repo)
        self.message_tracker.start()

        self.stats = StatisticsService(
            self.message_repo, self.voice_repo, self.reaction_repo,
            self.presence_repo, self.guild_repo,
        )

        for extension in (
            "cogs.tracking", "cogs.stats", "cogs.wrapped", "cogs.social",
            "cogs.leaderboard", "cogs.settings", "cogs.dev",
        ):
            await self.load_extension(extension)

        if config.dev_guild_id:
            guild_obj = discord.Object(id=config.dev_guild_id)
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            log.info("synced %d commands to dev guild", len(synced))
        else:
            synced = await self.tree.sync()
            log.info("synced %d commands globally", len(synced))

    async def on_ready(self) -> None:
        log.info("connected as %s", self.user)

    async def close(self) -> None:
        log.info("shutting down, flushing pending activity...")
        await self.message_tracker.stop()
        await self.voice_tracker.flush_all_open(self.get_guild_settings)
        await self.db.close()
        await super().close()


async def main() -> None:
    bot = Replay()
    async with bot:
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
