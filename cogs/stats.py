from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from ui.components import ReplayContainer, ReplayView, StatRow, action_row, header_text, not_enough_data_view, stat_block
from utils.formatting import format_duration, format_emoji_key, format_hour, format_number


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="your Replay overview")
    async def profile(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await self._send_profile(interaction, interaction.user)

    async def _send_profile(self, interaction: discord.Interaction, target: discord.Member) -> None:
        profile = await self.bot.stats.build_profile(interaction.guild_id, target.id)

        since_label = "recently"
        if profile.tracking_since:
            dt = datetime.fromisoformat(profile.tracking_since)
            since_label = dt.strftime("%b %-d, %Y") if dt.day > 9 else dt.strftime("%b %-d, %Y")

        rows = [
            StatRow("messages", format_number(profile.total_messages)),
            StatRow("voice time", format_duration(int(profile.voice_hours_total * 3600))),
            StatRow("active days", str(profile.active_days)),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text("REPLAY", f"tracking since {since_label}")),
            discord.ui.TextDisplay(f"### {target.display_name}"),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
            discord.ui.Separator(),
            discord.ui.TextDisplay(f"**{profile.personality}**\n-# {profile.personality_desc}"),
            action_row(
                discord.ui.Button(label="wrapped", style=discord.ButtonStyle.secondary, custom_id=f"replay:wrapped:{target.id}"),
                discord.ui.Button(label="compare", style=discord.ButtonStyle.secondary, custom_id=f"replay:compare:{target.id}"),
            ),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)

    @app_commands.command(name="messages", description="see your message stats")
    async def messages(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        guild_id, user_id = interaction.guild_id, interaction.user.id

        if not await self.bot.stats.has_enough_data(guild_id, user_id):
            await interaction.followup.send(view=not_enough_data_view(
                "Replay needs a little more activity before it can build this."
            ))
            return

        totals = await self.bot.message_repo.totals(guild_id, user_id)
        since_7d = _days_ago_iso(7)
        week_total = await self.bot.message_repo.totals_since(guild_id, user_id, since_7d)
        today_total = await self.bot.message_repo.totals_since(guild_id, user_id, _days_ago_iso(0))
        top_channel = await self.bot.message_repo.top_channel(guild_id, user_id)
        favorite_hour = await self.bot.message_repo.favorite_hour(guild_id, user_id)

        channel_mention = f"<#{top_channel[0]}>" if top_channel else "—"
        hour_label = format_hour(favorite_hour) if favorite_hour is not None else "—"

        rows = [
            StatRow("this week", format_number(week_total)),
            StatRow("today", format_number(today_total)),
            StatRow("most active", channel_mention),
            StatRow("favorite hour", hour_label),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text(f"{format_number(totals['total'])} total", "messages")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)

    @app_commands.command(name="vcstats", description="see your voice activity")
    async def vcstats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        guild_id, user_id = interaction.guild_id, interaction.user.id

        total = await self.bot.voice_repo.total_seconds(guild_id, user_id)
        if total == 0:
            await interaction.followup.send(view=not_enough_data_view(
                "I haven't seen enough VC activity for you."
            ))
            return

        today = await self.bot.voice_repo.seconds_since(guild_id, user_id, _days_ago_iso(0))
        week = await self.bot.voice_repo.seconds_since(guild_id, user_id, _days_ago_iso(7))
        month = await self.bot.voice_repo.seconds_since(guild_id, user_id, _days_ago_iso(30))
        longest = await self.bot.voice_repo.longest_session(guild_id, user_id)
        favorite_channel = await self.bot.voice_repo.favorite_channel(guild_id, user_id)
        session_count = await self.bot.voice_repo.session_count(guild_id, user_id)

        channel_mention = f"<#{favorite_channel}>" if favorite_channel else "—"

        rows = [
            StatRow("today", format_duration(today)),
            StatRow("this week", format_duration(week)),
            StatRow("this month", format_duration(month)),
            StatRow("all time", format_duration(total)),
            StatRow("longest session", format_duration(longest)),
            StatRow("favorite channel", channel_mention),
            StatRow("sessions", format_number(session_count)),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text("voice activity")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)


    @app_commands.command(name="server", description="see this server's Replay stats")
    async def server(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        guild_id = interaction.guild_id

        message_totals = await self.bot.message_repo.guild_totals(guild_id)
        vc_total = await self.bot.voice_repo.guild_total_seconds(guild_id)
        top_emoji = await self.bot.reaction_repo.guild_top_emoji(guild_id)

        top_channel = message_totals["top_channel_id"]
        channel_mention = f"<#{top_channel}>" if top_channel else "—"

        rows = [
            StatRow("total messages", format_number(message_totals["total_messages"])),
            StatRow("total voice time", format_duration(vc_total)),
            StatRow("busiest day", message_totals["busiest_day"] or "—"),
            StatRow("most active channel", channel_mention),
            StatRow("top reaction", format_emoji_key(top_emoji[0]) if top_emoji else "—"),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text("REPLAY", interaction.guild.name)),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)


def _days_ago_iso(days: int) -> str:
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


async def setup(bot):
    await bot.add_cog(Stats(bot))
