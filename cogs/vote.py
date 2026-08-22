"""
/vote -- points users at the listing page. VOTE_URL is a placeholder in
utils/config.py right now; swap it once the top.gg (or similar) page exists.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VOTE_URL
from utils.layout import LogLayout
from utils.views import JumpButton


class Vote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vote", description="Support the bot by voting for it.")
    async def vote(self, interaction: discord.Interaction):
        view = LogLayout(
            emoji_key="vote",
            title="Vote for the Bot",
            color=self.bot.theme_color,
            description="Voting takes a few seconds and helps the bot reach more servers.",
            fields=[],
            buttons=[JumpButton("Vote Now", VOTE_URL)],
        )
        await interaction.response.send_message(view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Vote(bot))
