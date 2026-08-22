"""
Entry point. Loads config, spins up the database, and boots every cog.
Keep this file thin -- actual logic lives in cogs/ and utils/.
"""

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

from utils.database import Database
from utils.config import THEME_COLOR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bot")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    log.critical("BOT_TOKEN is not set. Add it to your environment or a .env file.")
    sys.exit(1)

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
INTENTS.voice_states = True
INTENTS.moderation = True


class LoggerBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=INTENTS,
            help_command=None,
        )
        self.db: Database | None = None
        self.theme_color = THEME_COLOR

    async def setup_hook(self):
        self.db = Database("data/logger.sqlite3")
        await self.db.connect()

        for ext in (
            "cogs.events.messages",
            "cogs.events.members",
            "cogs.events.moderation",
            "cogs.events.channels",
            "cogs.events.roles",
            "cogs.events.voice",
            "cogs.events.invites",
            "cogs.events.server",
            "cogs.settings",
            "cogs.vote",
            "cogs.help",
        ):
            try:
                await self.load_extension(ext)
                log.info("Loaded extension: %s", ext)
            except Exception:
                log.exception("Failed to load extension: %s", ext)

        synced = await self.tree.sync()
        log.info("Synced %d application commands.", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="server activity"
            )
        )


async def main():
    os.makedirs("data", exist_ok=True)
    bot = LoggerBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
