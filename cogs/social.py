from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from services.duo import DuoInputs, best_shared_hour, compute_duo_score
from ui.components import ReplayContainer, ReplayView, StatRow, header_text, not_enough_data_view, stat_block
from utils.formatting import format_duration, format_hour_range, format_number


class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="aura", description="your Replay activity identity")
    async def aura(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        guild_id, user_id = interaction.guild_id, interaction.user.id

        if not await self.bot.stats.has_enough_data(guild_id, user_id):
            await interaction.followup.send(view=not_enough_data_view(
                "Replay needs a little more activity before it can build this."
            ))
            return

        profile = await self.bot.stats.build_profile(guild_id, user_id)
        night_hours = await self.bot.message_repo.active_hours_set(guild_id, user_id)
        night_frac = len([h for h in night_hours if h < 5]) / max(len(night_hours), 1)

        rows = [
            StatRow("messages", format_number(profile.total_messages)),
            StatRow("vc", format_duration(int(profile.voice_hours_total * 3600))),
            StatRow("night activity", f"{round(night_frac * 100)}%"),
            StatRow("type", profile.personality.replace("The ", "").lower()),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text(f"{interaction.user.display_name}'s aura")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
            discord.ui.Separator(),
            discord.ui.TextDisplay(f"-# aura\n# {profile.aura_score}"),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)

    @app_commands.command(name="duo", description="see your Replay with someone")
    @app_commands.describe(user="the person to compare with")
    async def duo(self, interaction: discord.Interaction, user: discord.Member) -> None:
        await interaction.response.defer()
        guild_id = interaction.guild_id
        a, b = interaction.user, user

        if a.id == b.id:
            await interaction.followup.send("that's just... your profile. try `/profile` instead.")
            return

        if not (await self.bot.stats.has_enough_data(guild_id, a.id)
                and await self.bot.stats.has_enough_data(guild_id, b.id)):
            await interaction.followup.send(view=not_enough_data_view(
                "Replay needs more activity from both of you before it can build this."
            ))
            return

        vc_together = await self.bot.voice_repo.pair_seconds(guild_id, a.id, b.id)
        hours_a = await self.bot.message_repo.active_hours_set(guild_id, a.id)
        hours_b = await self.bot.message_repo.active_hours_set(guild_id, b.id)
        channels_a = await self.bot.message_repo.channels_used(guild_id, a.id)
        channels_b = await self.bot.message_repo.channels_used(guild_id, b.id)
        days_a = await self.bot.message_repo.active_dates_set(guild_id, a.id)
        days_b = await self.bot.message_repo.active_dates_set(guild_id, b.id)

        score, _ = compute_duo_score(DuoInputs(
            vc_seconds_together=vc_together,
            hours_a=hours_a, hours_b=hours_b,
            channels_a=channels_a, channels_b=channels_b,
            active_days_a=days_a, active_days_b=days_b,
        ))
        shared_hour = best_shared_hour(hours_a, hours_b)
        shared_channels = channels_a & channels_b
        top_shared_channel = next(iter(shared_channels), None)
        shared_days = len(days_a & days_b)

        rows = [
            StatRow("vc together", format_duration(vc_together)),
            StatRow("your hour", format_hour_range(shared_hour) if shared_hour is not None else "—"),
            StatRow("your spot", f"<#{top_shared_channel}>" if top_shared_channel else "—"),
            StatRow("shared active days", str(shared_days)),
        ]

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text("REPLAY DUO", f"{a.display_name} + {b.display_name}")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(f"-# duo score\n# {score}%"),
            discord.ui.Separator(),
            discord.ui.TextDisplay(stat_block(rows)),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)

    @app_commands.command(name="compare", description="side-by-side stats with someone")
    @app_commands.describe(user="the person to compare with")
    async def compare(self, interaction: discord.Interaction, user: discord.Member) -> None:
        await interaction.response.defer()
        guild_id = interaction.guild_id
        a, b = interaction.user, user

        profile_a = await self.bot.stats.build_profile(guild_id, a.id)
        profile_b = await self.bot.stats.build_profile(guild_id, b.id)
        hours_a = await self.bot.message_repo.active_hours_set(guild_id, a.id)
        hours_b = await self.bot.message_repo.active_hours_set(guild_id, b.id)
        night_a = len([h for h in hours_a if h < 5]) / max(len(hours_a), 1)
        night_b = len([h for h in hours_b if h < 5]) / max(len(hours_b), 1)

        def line(label: str, va: str, vb: str) -> str:
            return f"-# {label}\n**{va}**  ·  **{vb}**"

        body = "\n\n".join([
            line("messages", format_number(profile_a.total_messages), format_number(profile_b.total_messages)),
            line("vc", format_duration(int(profile_a.voice_hours_total * 3600)),
                 format_duration(int(profile_b.voice_hours_total * 3600))),
            line("active days", str(profile_a.active_days), str(profile_b.active_days)),
            line("night %", f"{round(night_a * 100)}%", f"{round(night_b * 100)}%"),
        ])

        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text(f"{a.display_name} vs {b.display_name}")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(body),
        )
        view.add_item(container)
        await interaction.followup.send(view=view)


async def setup(bot):
    await bot.add_cog(Social(bot))
