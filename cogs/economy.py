import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd
import utils.ui as ui


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="View rods available for purchase.")
    async def shop(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        await interaction.response.send_message(view=ui.shop_view(user_row=user))

    @app_commands.command(name="buy", description="Buy the next rod tier.")
    @app_commands.describe(tier="Rod tier to purchase")
    async def buy(self, interaction: discord.Interaction, tier: int):
        if tier not in gd.RODS:
            await interaction.response.send_message(
                view=ui.error_view("That rod tier doesn't exist."), ephemeral=True
            )
            return

        uid = interaction.user.id
        async with db.user_lock(uid):
            user = await db.get_user(uid)
            if tier <= user["rod_tier"]:
                await interaction.response.send_message(
                    view=ui.error_view("You already own that rod (or better)."), ephemeral=True
                )
                return
            if tier != user["rod_tier"] + 1:
                await interaction.response.send_message(
                    view=ui.error_view(
                        f"You need to buy rods in order — you're currently on Tier {user['rod_tier']}."
                    ),
                    ephemeral=True,
                )
                return

            price = gd.RODS[tier]["price"]
            spent = await db.try_spend(uid, price)
            if not spent:
                await interaction.response.send_message(
                    view=ui.error_view(
                        f"You need **{price:,} {config.CURRENCY_NAME}** for the "
                        f"{gd.RODS[tier]['name']} (you have {user['balance']:,})."
                    ),
                    ephemeral=True,
                )
                return
            await db.set_rod_tier(uid, tier)

        await interaction.response.send_message(
            view=ui.buy_view(rod_name=gd.RODS[tier]["name"], max_rarity=gd.RODS[tier]["max_rarity"])
        )

    @app_commands.command(name="leaderboard", description="See the top Nibble players.")
    @app_commands.describe(category="Which leaderboard to view")
    @app_commands.choices(category=[
        app_commands.Choice(name="Wealth", value="wealth"),
        app_commands.Choice(name="Collection Size", value="collection"),
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        cat = category.value if category else "wealth"
        rows = await db.leaderboard_balance() if cat == "wealth" else await db.leaderboard_collection()

        await interaction.response.send_message(
            view=ui.leaderboard_view(category=cat, rows=rows, fish_total=len(gd.FISH))
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
