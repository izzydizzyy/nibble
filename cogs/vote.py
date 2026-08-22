"""
/vote -- points users at the listing page. VOTE_URL is a placeholder in
utils/config.py right now; swap it once the top.gg (or similar) page exists.
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import VOTE_URL
from utils.embeds import log_embed


class Vote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vote", description="Support the bot by voting for it.")
    async def vote(self, interaction: discord.Interaction):
        embed = log_embed(
            title="Vote for the Bot",
            color=self.bot.theme_color,
            description="Voting takes a few seconds and helps the bot reach more servers.",
            fields=[],
        )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="Vote Now", style=discord.ButtonStyle.link, url=VOTE_URL)
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Vote(bot))
