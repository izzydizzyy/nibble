import time

import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd
import utils.ui as ui


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your Nibbles balance.")
    async def balance(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        lines = [
            ui.BRAND,
            f"### {config.CURRENCY_EMOJI} Balance",
            f"You have **{user['balance']:,} {config.CURRENCY_NAME}**.",
        ]
        await interaction.response.send_message(view=ui.SimpleView(lines, accent=0x2B2D31))

    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        uid = interaction.user.id
        async with db.user_lock(uid):
            user = await db.get_user(uid)
            now = time.time()
            last = user["last_daily"]
            streak = user["daily_streak"]

            if last is not None:
                elapsed_h = (now - last) / 3600
                if elapsed_h < gd.DAILY_COOLDOWN_HOURS:
                    remaining_h = gd.DAILY_COOLDOWN_HOURS - elapsed_h
                    await interaction.response.send_message(
                        view=ui.cooldown_view(remaining_h * 3600, kind="daily"),
                        ephemeral=True,
                    )
                    return
                # Within grace window -> streak continues, else resets.
                if elapsed_h > gd.DAILY_STREAK_GRACE_HOURS:
                    streak = 0

            streak += 1
            bonus = min(
                streak * gd.DAILY_STREAK_BONUS_PER_DAY,
                gd.DAILY_STREAK_BONUS_CAP,
            )
            reward = gd.DAILY_BASE_REWARD + bonus

            await db.set_daily(uid, now, streak)
            await db.add_balance(uid, reward)

        await interaction.response.send_message(view=ui.daily_view(reward=reward, streak=streak))

    @app_commands.command(name="profile", description="View your Nibble profile.")
    @app_commands.describe(user="Whose profile to view (defaults to you)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        u = await db.get_user(target.id)
        inv = await db.get_inventory(target.id)

        await interaction.response.send_message(
            view=ui.profile_view(
                target=target,
                user_row=u,
                unique_fish=len(inv),
                total_species=len(gd.FISH),
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
