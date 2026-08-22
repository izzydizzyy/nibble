"""
/settings -- one entry point, two follow-up interactions:
  1. a channel select to set the default log channel
  2. a group select to bulk-toggle event categories

Every response here is a CV2 LogLayout too, so the config UI matches
the log output instead of looking like a bolted-on legacy embed.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import EVENT_GROUPS
from utils.layout import LogLayout


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
        view = LogLayout(
            emoji_key="success",
            title="Log Channel Set",
            color=self.bot.theme_color,
            fields=[("Channel", channel.mention)],
        )
        await interaction.response.edit_message(view=view)


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
        view = LogLayout(
            emoji_key="success",
            title="Event Categories Updated",
            color=self.bot.theme_color,
            fields=[("Disabled", summary)],
        )
        await interaction.response.edit_message(view=view)


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    settings_group = app_commands.Group(
        name="settings", description="Configure the logging system for this server."
    )

    @settings_group.command(name="channel", description="Set the default channel logs are sent to.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction):
        view = LogLayout(
            emoji_key="settings",
            title="Set Log Channel",
            color=self.bot.theme_color,
            fields=[("Instructions", "Pick a channel from the dropdown below.")],
        )
        await interaction.response.send_message(
            view=_combine(view, ChannelSelect(self.bot)), ephemeral=True
        )

    @settings_group.command(name="events", description="Enable or disable categories of logged events.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def events(self, interaction: discord.Interaction):
        view = LogLayout(
            emoji_key="settings",
            title="Toggle Event Categories",
            color=self.bot.theme_color,
            fields=[
                (
                    "Instructions",
                    "Select any categories you want to turn off. Leave empty to keep everything on.",
                )
            ],
        )
        await interaction.response.send_message(
            view=_combine(view, GroupToggleSelect(self.bot)), ephemeral=True
        )

    @settings_group.command(name="status", description="View the current logging configuration.")
    async def status(self, interaction: discord.Interaction):
        cfg = await self.bot.db.get_guild_config(interaction.guild_id)
        channel = interaction.guild.get_channel(cfg["log_channel"]) if cfg["log_channel"] else None
        view = LogLayout(
            emoji_key="settings",
            title="Logging Status",
            color=self.bot.theme_color,
            fields=[
                ("Enabled", "Yes" if cfg["enabled"] else "No"),
                ("Log Channel", channel.mention if channel else "*Not set*"),
            ],
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    @settings_group.command(name="toggle", description="Turn all logging on or off.")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(enabled="Whether logging should be active")
    async def toggle(self, interaction: discord.Interaction, enabled: bool):
        await self.bot.db.set_enabled(interaction.guild_id, enabled)
        view = LogLayout(
            emoji_key="success",
            title="Logging Toggled",
            color=self.bot.theme_color,
            fields=[("Status", "Enabled" if enabled else "Disabled")],
        )
        await interaction.response.send_message(view=view, ephemeral=True)


def _combine(layout: LogLayout, select: discord.ui.Select) -> LogLayout:
    """Append a select menu, wrapped in its own action row, to an existing CV2 container."""
    container = layout.children[0]
    container.add_item(discord.ui.ActionRow(select))
    return layout


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
