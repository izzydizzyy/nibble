import time

import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd


class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your Nibbles balance.")
    async def balance(self, interaction: discord.Interaction):
        user = await db.get_user(interaction.user.id)
        await interaction.response.send_message(
            f"{config.CURRENCY_EMOJI} You have **{user['balance']:,} {config.CURRENCY_NAME}**."
        )

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
                    remaining = gd.DAILY_COOLDOWN_HOURS - elapsed_h
                    h, m = int(remaining), int((remaining % 1) * 60)
                    await interaction.response.send_message(
                        f"⏳ You already claimed today. Try again in **{h}h {m}m**.",
                        ephemeral=True,
                    )
                    return

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

        embed = discord.Embed(
            title="🐾 Daily Reward Claimed!",
            description=(
                f"You received **{reward:,} {config.CURRENCY_NAME}** "
                f"{config.CURRENCY_EMOJI}\n"
                f"🔥 Streak: **{streak}** day(s)"
            ),
            color=0xFFC107,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your Nibble profile.")
    @app_commands.describe(user="Whose profile to view (defaults to you)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        u = await db.get_user(target.id)
        inv = await db.get_inventory(target.id)
        unique_fish = len(inv)
        total_species = len(gd.FISH)
        rod = gd.RODS[u["rod_tier"]]

        embed = discord.Embed(title=f"🐱 {target.display_name}'s Profile", color=0x03A9F4)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name="Balance", value=f"{config.CURRENCY_EMOJI} {u['balance']:,}", inline=True
        )
        embed.add_field(name="Rod", value=rod["name"], inline=True)
        embed.add_field(name="Daily Streak", value=f"🔥 {u['daily_streak']}", inline=True)
        embed.add_field(
            name="Collection",
            value=f"📖 {unique_fish}/{total_species} species discovered",
            inline=True,
        )
        embed.add_field(name="Total Fish Caught", value=f"🎣 {u['total_fish']:,}", inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
