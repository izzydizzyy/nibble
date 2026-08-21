import asyncio
import logging
import logging.handlers
import os

import discord
from discord.ext import commands

import config
import database as db

os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)


logger = logging.getLogger("nibble")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"
))
file_handler = logging.handlers.RotatingFileHandler(
    "logs/nibble.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(console_handler.formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)
discord_logger.addHandler(file_handler)

COGS = ["cogs.core", "cogs.fishing", "cogs.inventory", "cogs.economy"]


class NibbleBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await db.init_db()
        logger.info("Database ready at %s", config.DATABASE_PATH)

        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info("Loaded cog: %s", cog)
            except Exception:
                logger.exception("Failed to load cog: %s", cog)

        if config.DEV_GUILD_ID:
            guild = discord.Object(id=int(config.DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d commands to dev guild %s", len(synced), config.DEV_GUILD_ID)
        else:
            synced = await self.tree.sync()
            logger.info("Synced %d commands globally (may take up to 1hr to appear)", len(synced))

    async def on_ready(self):
        logger.info("Logged in as %s (id: %s)", self.user, self.user.id)
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="/fish 🎣")
        )

    async def on_command_error(self, ctx, error):
        logger.exception("Prefix command error", exc_info=error)

    async def close(self):
        await db.close_db()
        await super().close()


bot = NibbleBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    logger.error("Slash command error in /%s: %s", interaction.command.name if interaction.command else "?", error)

    if isinstance(error, discord.app_commands.CommandOnCooldown):
        msg = f"⏳ Slow down — try again in {error.retry_after:.1f}s."
    else:
        msg = "⚠️ Something went wrong running that command. It's been logged."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.HTTPException:
        pass


def main():
    try:
        bot.run(config.DISCORD_TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("Login failed: check your DISCORD_TOKEN in .env")


if __name__ == "__main__":
    main()
