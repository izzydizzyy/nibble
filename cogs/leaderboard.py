from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ui.components import ReplayContainer, ReplayView, header_text
from utils.formatting import format_duration, format_number
from utils.time import period_start

CATEGORIES = {
    "messages": "messages",
    "vc": "voice time",
    "active_days": "active days",
    "streaks": "current streak",
}


class CategorySelect(discord.ui.Select):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        options = [discord.SelectOption(label=label, value=key) for key, label in CATEGORIES.items()]
        super().__init__(placeholder="switch category", options=options, custom_id="replay:leaderboard:select")

    async def callback(self, interaction: discord.Interaction) -> None:
        category = self.values[0]
        body = await build_leaderboard_body(self.bot, self.guild_id, category, interaction.guild)
        view = LeaderboardView(self.bot, self.guild_id, category)
        view.container.children[1].content = body  # type: ignore[attr-defined]
        await interaction.response.edit_message(view=view)


class LeaderboardView(discord.ui.LayoutView):
    def __init__(self, bot, guild_id: int, category: str):
        super().__init__(timeout=300)
        self.bot = bot
        select = CategorySelect(bot, guild_id)
        select.values = [category]
        self.container = ReplayContainer(
            discord.ui.TextDisplay(header_text("leaderboard", CATEGORIES[category])),
            discord.ui.TextDisplay("loading..."),
            discord.ui.ActionRow(select),
        )
        self.add_item(self.container)


async def build_leaderboard_body(bot, guild_id: int, category: str, guild: discord.Guild) -> str:
    if category == "messages":
        rows = await bot.message_repo.leaderboard(guild_id, None)
        formatter = format_number
    elif category == "vc":
        rows = await bot.voice_repo.leaderboard(guild_id, None)
        formatter = format_duration
    elif category == "active_days":
        top = await bot.message_repo.leaderboard(guild_id, None, limit=25)
        rows = []
        for r in top:
            days = await bot.message_repo.active_days(guild_id, r["user_id"])
            rows.append({"user_id": r["user_id"], "value": days})
        rows.sort(key=lambda r: r["value"], reverse=True)
        rows = rows[:10]
        formatter = str
    else:  # streaks
        top = await bot.message_repo.leaderboard(guild_id, None, limit=25)
        rows = []
        for r in top:
            streak = await bot.message_repo.streak(guild_id, r["user_id"])
            rows.append({"user_id": r["user_id"], "value": streak["current"]})
        rows.sort(key=lambda r: r["value"], reverse=True)
        rows = rows[:10]
        formatter = lambda v: f"{v} days"

    if not rows:
        return "nothing tracked yet"

    lines = []
    for i, row in enumerate(rows, start=1):
        lines.append(f"**{i}.** <@{row['user_id']}> — {formatter(row['value'])}")
    return "\n".join(lines)


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="see who's on top")
    @app_commands.describe(category="what to rank by")
    @app_commands.choices(category=[
        app_commands.Choice(name=label, value=key) for key, label in CATEGORIES.items()
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "messages") -> None:
        await interaction.response.defer()
        body = await build_leaderboard_body(self.bot, interaction.guild_id, category, interaction.guild)
        view = LeaderboardView(self.bot, interaction.guild_id, category)
        view.container.children[1].content = body  # type: ignore[attr-defined]
        await interaction.followup.send(view=view)


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
