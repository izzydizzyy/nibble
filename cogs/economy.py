import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="View rods available for purchase.")
    async def shop(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        lines = []
        for tier, rod in gd.RODS.items():
            owned = "✅ Owned" if tier <= user["rod_tier"] else f"{rod['price']:,} {config.CURRENCY_EMOJI}"
            current = " ⬅️ *equipped*" if tier == user["rod_tier"] else ""
            lines.append(
                f"**Tier {tier}: {rod['name']}** — up to {rod['max_rarity'].title()} fish\n"
                f"{owned}{current}"
            )

        embed = discord.Embed(
            title="🛒 Nibble's Shop — Rods",
            description="\n\n".join(lines),
            color=0x8BC34A,
        )
        embed.set_footer(text="Buy a rod with /buy <tier>")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy the next rod tier.")
    @app_commands.describe(tier="Rod tier to purchase")
    async def buy(self, interaction: discord.Interaction, tier: int):
        if tier not in gd.RODS:
            await interaction.response.send_message("That rod tier doesn't exist.", ephemeral=True)
            return

        uid = interaction.user.id
        async with db.user_lock(uid):
            user = await db.get_user(uid)
            if tier <= user["rod_tier"]:
                await interaction.response.send_message("You already own that rod (or better).", ephemeral=True)
                return
            if tier != user["rod_tier"] + 1:
                await interaction.response.send_message(
                    f"You need to buy rods in order — you're currently on Tier {user['rod_tier']}.",
                    ephemeral=True,
                )
                return

            price = gd.RODS[tier]["price"]
            spent = await db.try_spend(uid, price)
            if not spent:
                await interaction.response.send_message(
                    f"You need **{price:,} {config.CURRENCY_NAME}** for that (you have {user['balance']:,}).",
                    ephemeral=True,
                )
                return
            await db.set_rod_tier(uid, tier)

        await interaction.response.send_message(
            f"🎣 You bought the **{gd.RODS[tier]['name']}**! You can now catch up to "
            f"**{gd.RODS[tier]['max_rarity'].title()}** fish."
        )

    @app_commands.command(name="leaderboard", description="See the top Nibble players.")
    @app_commands.describe(category="Which leaderboard to view")
    @app_commands.choices(category=[
        app_commands.Choice(name="Wealth", value="wealth"),
        app_commands.Choice(name="Collection Size", value="collection"),
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: app_commands.Choice[str] = None):
        cat = category.value if category else "wealth"

        if cat == "wealth":
            rows = await db.leaderboard_balance()
            title = f"🏆 Richest Nibblers"
            lines = [
                f"**#{i+1}** <@{r['user_id']}> — {r['balance']:,} {config.CURRENCY_EMOJI}"
                for i, r in enumerate(rows)
            ]
        else:
            rows = await db.leaderboard_collection()
            title = f"🏆 Top Collectors"
            lines = [
                f"**#{i+1}** <@{r['user_id']}> — {r['unique_fish']}/{len(gd.FISH)} species"
                for i, r in enumerate(rows)
            ]

        if not lines:
            lines = ["No data yet — be the first!"]

        embed = discord.Embed(title=title, description="\n".join(lines), color=0xFFD700)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
