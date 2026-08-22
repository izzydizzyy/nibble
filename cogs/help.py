import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import log_embed


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="List available commands.")
    async def help(self, interaction: discord.Interaction):
        embed = log_embed(
            title="Command Reference",
            color=self.bot.theme_color,
            description="Configuration is done through `/settings`, everything else is standalone.",
            fields=[
                ("/settings channel", "Set the default channel logs are sent to.", False),
                ("/settings events", "Enable or disable categories of logged events.", False),
                ("/settings toggle", "Turn all logging on or off.", False),
                ("/settings status", "View the current logging configuration.", False),
                ("/vote", "Get a link to vote for the bot.", False),
            ],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
