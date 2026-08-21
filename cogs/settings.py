from __future__ import annotations

from zoneinfo import ZoneInfoNotFoundError, available_timezones

import discord
from discord import app_commands
from discord.ext import commands

from ui.components import ReplayContainer, ReplayView, header_text
from utils.time import get_zone

VALID_ZONES = available_timezones()

PRIVACY_TEXT = (
    "Replay tracks activity in servers it's added to, starting from the moment it joins. "
    "It never sees anything from before that.\n\n"
    "**what's stored:** message counts per channel/day/hour (not message content), "
    "voice session lengths, reactions given, and game/listening activity Discord's presence "
    "system shares with the bot.\n\n"
    "**what's never stored:** DMs, message content, tokens or credentials, or anything from "
    "before Replay joined.\n\n"
    "run `/privacy delete-my-data` to erase everything Replay has on you in this server."
)


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    settings_group = app_commands.Group(name="settings", description="configure Replay for this server")

    @settings_group.command(name="timezone", description="set the timezone Replay uses for this server")
    @app_commands.describe(zone="an IANA timezone, e.g. America/New_York")
    @app_commands.default_permissions(manage_guild=True)
    async def timezone(self, interaction: discord.Interaction, zone: str) -> None:
        if zone not in VALID_ZONES:
            await interaction.response.send_message(
                f"`{zone}` isn't a recognized timezone. try something like `America/New_York` or `Europe/London`.",
                ephemeral=True,
            )
            return
        await self.bot.guild_repo.set_timezone(interaction.guild_id, zone)
        self.bot.invalidate_settings(interaction.guild_id)
        await interaction.response.send_message(f"timezone set to `{zone}`.", ephemeral=True)

    @settings_group.command(name="tracking", description="turn a tracking category on or off")
    @app_commands.describe(category="which category", enabled="on or off")
    @app_commands.choices(category=[
        app_commands.Choice(name="messages", value="track_messages"),
        app_commands.Choice(name="voice", value="track_voice"),
        app_commands.Choice(name="presence (games/music)", value="track_presence"),
        app_commands.Choice(name="exclude solo VC sessions", value="exclude_solo_vc"),
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def tracking(self, interaction: discord.Interaction, category: str, enabled: bool) -> None:
        await self.bot.guild_repo.set_tracking_flag(interaction.guild_id, category, enabled)
        self.bot.invalidate_settings(interaction.guild_id)
        await interaction.response.send_message(
            f"{'enabled' if enabled else 'disabled'} `{category}`.", ephemeral=True
        )

    privacy_group = app_commands.Group(name="privacy", description="what Replay stores about you")

    @privacy_group.command(name="info", description="see what Replay stores")
    async def privacy_info(self, interaction: discord.Interaction) -> None:
        view = ReplayView()
        container = ReplayContainer(
            discord.ui.TextDisplay(header_text("privacy")),
            discord.ui.Separator(),
            discord.ui.TextDisplay(PRIVACY_TEXT),
        )
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)

    @privacy_group.command(name="delete-my-data", description="erase everything Replay has tracked about you here")
    async def delete_my_data(self, interaction: discord.Interaction) -> None:
        await self.bot.guild_repo.delete_all_user_data(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message(
            "done — everything Replay tracked about you in this server is gone.", ephemeral=True
        )

    @privacy_group.command(name="opt-out", description="stop Replay from tracking your activity here")
    async def opt_out(self, interaction: discord.Interaction) -> None:
        await self.bot.guild_repo.set_opt_out(interaction.guild_id, interaction.user.id, True)
        await interaction.response.send_message("you're opted out — Replay will stop tracking you here.", ephemeral=True)

    @privacy_group.command(name="opt-in", description="let Replay track your activity here again")
    async def opt_in(self, interaction: discord.Interaction) -> None:
        await self.bot.guild_repo.set_opt_out(interaction.guild_id, interaction.user.id, False)
        await interaction.response.send_message("you're opted back in.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Settings(bot))
