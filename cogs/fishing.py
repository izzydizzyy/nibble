import time

import discord
from discord import app_commands
from discord.ext import commands

import database as db
import game_data as gd
import utils.ui as ui
from utils.rolls import roll_fish, roll_weight


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
                    view=ui.cooldown_view(remaining, kind="fish"), ephemeral=True
                )
                return

            fish_id, name, emoji, rarity, value, min_rod = roll_fish(user["rod_tier"])
            prior_qty = await db.get_fish_qty(uid, fish_id)
            is_new = prior_qty == 0

            await db.set_last_fish(uid, now)
            await db.add_fish(uid, fish_id, 1)

            unique_species = None
            if is_new:
                unique_species = len(await db.get_inventory(uid))

        await interaction.response.send_message(
            view=ui.catch_view(
                name=name,
                emoji=emoji,
                rarity=rarity,
                value=value,
                is_new=is_new,
                owned_qty=prior_qty + 1,
                weight=roll_weight(rarity),
                unique_species=unique_species,
                total_species=len(gd.FISH),
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Fishing(bot))
