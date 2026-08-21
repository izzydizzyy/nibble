import time

import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd
from utils.rolls import roll_fish


class Fishing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fish", description="Cast your rod and see what you catch.")
    async def fish(self, interaction: discord.Interaction):
        uid = interaction.user.id
        async with db.user_lock(uid):
            user = await db.get_user(uid)
            now = time.time()
            last = user["last_fish"]
            if last is not None and (now - last) < gd.FISH_COOLDOWN:
                remaining = gd.FISH_COOLDOWN - (now - last)
                await interaction.response.send_message(
                    f"⏳ Your line's still out. Try again in **{remaining:.0f}s**.",
                    ephemeral=True,
                )
                return

            fish_id, name, emoji, rarity, value, min_rod = roll_fish(user["rod_tier"])
            prior_qty = await db.get_fish_qty(uid, fish_id)

            await db.set_last_fish(uid, now)
            await db.add_fish(uid, fish_id, 1)

        rarity_info = gd.RARITIES[rarity]
        is_new = prior_qty == 0

        embed = discord.Embed(
            title=f"{emoji} You caught a {name}!",
            description=f"{rarity_info['emoji']} **{rarity.title()}** • worth {value:,} {config.CURRENCY_EMOJI}",
            color=rarity_info["color"],
        )
        if is_new:
            embed.add_field(name="✨ New Discovery!", value=f"Added **{name}** to your collection.")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fishing(bot))
