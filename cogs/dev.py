from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from config import config


def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in config.owner_ids
    return app_commands.check(predicate)


class Dev(commands.Cog):
    """Sample-data tooling so /wrapped, /aura, /duo can be tested without
    waiting weeks for real activity. Owner-gated and scoped to whatever
    guild/user runs it — never touches other members' real data."""

    def __init__(self, bot):
        self.bot = bot

    dev_group = app_commands.Group(name="dev", description="developer-only tools")

    @dev_group.command(name="seed-stats", description="[owner only] fill your profile with fake test data")
    @is_owner()
    async def seed_stats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        guild_id, user_id = interaction.guild_id, interaction.user.id
        await self.bot.guild_repo.ensure_guild(guild_id, interaction.guild.name)
        await self.bot.guild_repo.ensure_member(guild_id, user_id)

        channel_ids = [c.id for c in interaction.guild.text_channels[:5]] or [interaction.channel_id]
        now = datetime.now(timezone.utc)

        events = []
        for day_offset in range(30):
            day = (now - timedelta(days=day_offset)).date().isoformat()
            for _ in range(random.randint(5, 60)):
                hour = random.choices(range(24), weights=_night_owl_weights())[0]
                channel = random.choice(channel_ids)
                events.append((guild_id, user_id, channel, day, hour))
        await self.bot.message_repo.record_batch(events)
        for day_offset in range(min(12, 30)):
            day = (now - timedelta(days=day_offset)).date().isoformat()
            await self.bot.message_repo.bump_streak(guild_id, user_id, day)

        for _ in range(15):
            start = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 20))
            duration = random.randint(300, 3 * 3600)
            end = start + timedelta(seconds=duration)
            await self.bot.voice_repo.record_session(
                guild_id, user_id, channel_ids[0], start.isoformat(), end.isoformat(),
                duration, False, {start.date().isoformat(): duration},
            )

        for emoji in ["💀", "😭", "🔥", "👀"]:
            for _ in range(random.randint(2, 20)):
                await self.bot.reaction_repo.record(guild_id, user_id, emoji)

        await interaction.followup.send("seeded 30 days of fake activity for you. run `/wrapped` or `/aura`.", ephemeral=True)

    @dev_group.command(name="clear-seed", description="[owner only] wipe your test data in this server")
    @is_owner()
    async def clear_seed(self, interaction: discord.Interaction) -> None:
        await self.bot.guild_repo.delete_all_user_data(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message("cleared.", ephemeral=True)


def _night_owl_weights() -> list[int]:
    weights = [1] * 24
    for h in range(0, 5):
        weights[h] = 6
    return weights


async def setup(bot):
    await bot.add_cog(Dev(bot))
