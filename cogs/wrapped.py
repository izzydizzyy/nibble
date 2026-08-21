from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from renderers.wrapped import render_wrapped
from ui.components import ReplayContainer, ReplayView, not_enough_data_view
from utils.formatting import format_duration, format_hour, format_number
from utils.time import period_start


class Wrapped(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="wrapped", description="your Replay wrapped")
    @app_commands.describe(period="time window")
    @app_commands.choices(period=[
        app_commands.Choice(name="this week", value="week"),
        app_commands.Choice(name="this month", value="month"),
        app_commands.Choice(name="all time", value="all-time"),
    ])
    async def wrapped(self, interaction: discord.Interaction, period: str = "month") -> None:
        await interaction.response.defer()
        guild_id, user_id = interaction.guild_id, interaction.user.id

        if not await self.bot.stats.has_enough_data(guild_id, user_id):
            await interaction.followup.send(view=not_enough_data_view(
                "Replay needs a little more activity before it can build this."
            ))
            return

        tz_name = await self.bot.get_guild_timezone(guild_id)
        since = period_start(period, tz_name)

        if since:
            message_total = await self.bot.message_repo.totals_since(guild_id, user_id, since)
            vc_seconds = await self.bot.voice_repo.seconds_since(guild_id, user_id, since)
        else:
            message_total = (await self.bot.message_repo.totals(guild_id, user_id))["total"]
            vc_seconds = await self.bot.voice_repo.total_seconds(guild_id, user_id)

        favorite_hour = await self.bot.message_repo.favorite_hour(guild_id, user_id)
        top_channel = await self.bot.message_repo.top_channel(guild_id, user_id)
        top_emoji = await self.bot.reaction_repo.top_emoji(guild_id, user_id)
        streak = await self.bot.message_repo.streak(guild_id, user_id)
        profile = await self.bot.stats.build_profile(guild_id, user_id)

        period_labels = {"week": "this week", "month": "this month", "all-time": "all time"}
        channel = interaction.guild.get_channel(int(top_channel[0])) if top_channel else None

        stats = [
            ("messages sent", format_number(message_total)),
            ("voice time", format_duration(vc_seconds)),
            ("favorite hour", format_hour(favorite_hour) if favorite_hour is not None else "—"),
            ("favorite channel", f"#{channel.name}" if channel else "—"),
            ("longest streak", f"{streak['longest']} days"),
        ]

        image_bytes = await render_wrapped(
            username=interaction.user.display_name,
            period_label=period_labels.get(period, period),
            avatar_url=interaction.user.display_avatar.url,
            stats=stats,
            personality=profile.personality,
        )

        file = discord.File(image_bytes, filename="wrapped.png")
        view = ReplayView()
        container = ReplayContainer(
            discord.ui.MediaGallery(discord.MediaGalleryItem(media="attachment://wrapped.png")),
        )
        view.add_item(container)
        await interaction.followup.send(file=file, view=view)


async def setup(bot):
    await bot.add_cog(Wrapped(bot))
