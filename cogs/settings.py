"""
/settings -- one entry point, two follow-up interactions:
  1. a channel select to set the default log channel
  2. a group select to bulk-toggle event categories

Kept deliberately small. Per-event overrides exist in the DB layer already;
exposing every single one through slash commands isn't worth the clutter,
so /settings covers the 90% case and power users can ask for a specific
override via a follow-up command if they ever need it.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import EVENT_GROUPS
from utils.embeds import log_embed
from utils.config import SUCCESS_COLOR


class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            placeholder="Choose a log channel...",
            channel_types=[discord.ChannelType.text],
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        await self.bot.db.set_log_channel(interaction.guild_id, channel.id)
        embed = log_embed(
            title="Log Channel Set",
            color=SUCCESS_COLOR,
            fields=[("Channel", channel.mention, False)],
        )
        await interaction.response.edit_message(embed=embed, view=None)


class ChannelSelectView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=60)
        self.add_item(ChannelSelect(bot))


class GroupToggleSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        options = [
            discord.SelectOption(label=group.replace("_", " ").title(), value=group)
            for group in EVENT_GROUPS
        ]
        super().__init__(
            placeholder="Choose event categories to disable...",
            min_values=0,
            max_values=len(options),
            options=options,
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        disabled_groups = set(self.values)
        for group, events in EVENT_GROUPS.items():
            enabled = group not in disabled_groups
            for event_key in events:
                await self.bot.db.set_event_toggle(interaction.guild_id, event_key, enabled)

        summary = ", ".join(disabled_groups) if disabled_groups else "None"
        embed = log_embed(
            title="Event Categories Updated",
            color=SUCCESS_COLOR,
            fields=[("Disabled", summary, False)],
        )
        await interaction.response.edit_message(embed=embed, view=None)


class GroupToggleView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=60)
        self.add_item(GroupToggleSelect(bot))


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    settings_group = app_commands.Group(
        name="settings", description="Configure the logging system for this server."
    )

    @settings_group.command(name="channel", description="Set the default channel logs are sent to.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction):
        embed = log_embed(
            title="Set Log Channel",
            color=self.bot.theme_color,
            fields=[("Instructions", "Pick a channel from the dropdown below.", False)],
        )
        await interaction.response.send_message(
            embed=embed, view=ChannelSelectView(self.bot), ephemeral=True
        )

    @settings_group.command(name="events", description="Enable or disable categories of logged events.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def events(self, interaction: discord.Interaction):
        embed = log_embed(
            title="Toggle Event Categories",
            color=self.bot.theme_color,
            fields=[
                (
                    "Instructions",
                    "Select any categories you want to turn off. Leave empty to keep everything on.",
                    False,
                )
            ],
        )
        await interaction.response.send_message(
            embed=embed, view=GroupToggleView(self.bot), ephemeral=True
        )

    @settings_group.command(name="status", description="View the current logging configuration.")
    async def status(self, interaction: discord.Interaction):
        cfg = await self.bot.db.get_guild_config(interaction.guild_id)
        channel = interaction.guild.get_channel(cfg["log_channel"]) if cfg["log_channel"] else None
        embed = log_embed(
            title="Logging Status",
            color=self.bot.theme_color,
            fields=[
                ("Enabled", "Yes" if cfg["enabled"] else "No", True),
                ("Log Channel", channel.mention if channel else "*Not set*", True),
            ],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @settings_group.command(name="toggle", description="Turn all logging on or off.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(enabled="Whether logging should be active")
    async def toggle(self, interaction: discord.Interaction, enabled: bool):
        await self.bot.db.set_enabled(interaction.guild_id, enabled)
        embed = log_embed(
            title="Logging Toggled",
            color=SUCCESS_COLOR,
            fields=[("Status", "Enabled" if enabled else "Disabled", False)],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
