import discord
from discord import app_commands
from discord.ext import commands

import config
import database as db
import game_data as gd


class Inventory(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="See the fish you're holding.")
    async def inventory(self, interaction: discord.Interaction):
        uid = interaction.user.id
        rows = await db.get_inventory(uid)
        if not rows:
            await interaction.response.send_message(
                "Your bag is empty. Go `/fish` to catch something!", ephemeral=True
            )
            return

        lines = []
        total_value = 0
        for row in rows:
            f = gd.FISH_BY_ID[row["fish_id"]]
            _, name, emoji, rarity, value, _ = f
            qty = row["quantity"]
            total_value += value * qty
            lines.append(f"{emoji} **{name}** x{qty} — {gd.RARITIES[rarity]['emoji']} {rarity}")

        embed = discord.Embed(
            title=f"🎒 {interaction.user.display_name}'s Inventory",
            description="\n".join(lines[:25]),
            color=0x795548,
        )
        embed.set_footer(text=f"Total sell value: {total_value:,} {config.CURRENCY_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="collection", description="See your collection progress across all species.")
    async def collection(self, interaction: discord.Interaction):
        uid = interaction.user.id
        rows = {r["fish_id"]: r["quantity"] for r in await db.get_inventory(uid)}

        by_rarity: dict[str, list[str]] = {r: [] for r in gd.RARITY_ORDER}
        for fish_id, name, emoji, rarity, value, _ in gd.FISH:
            owned = rows.get(fish_id, 0)
            mark = f"{emoji} {name}" if owned > 0 else f"❓ ???"
            by_rarity[rarity].append(mark)

        embed = discord.Embed(
            title=f"📖 {interaction.user.display_name}'s Collection",
            description=f"{len(rows)}/{len(gd.FISH)} species discovered",
            color=0x00BCD4,
        )
        for rarity in gd.RARITY_ORDER:
            entries = by_rarity[rarity]
            embed.add_field(
                name=f"{gd.RARITIES[rarity]['emoji']} {rarity.title()}",
                value="\n".join(entries) or "—",
                inline=True,
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Sell fish from your inventory.")
    @app_commands.describe(fish="Name of the fish to sell", quantity="How many to sell (default 1)")
    async def sell(self, interaction: discord.Interaction, fish: str, quantity: int = 1):
        if quantity < 1:
            await interaction.response.send_message("Quantity must be at least 1.", ephemeral=True)
            return

        match = next((f for f in gd.FISH if f[1].lower() == fish.lower()), None)
        if not match:
            await interaction.response.send_message(
                f"Couldn't find a fish named **{fish}**. Check `/inventory` for exact names.",
                ephemeral=True,
            )
            return

        fish_id, name, emoji, rarity, value, _ = match
        uid = interaction.user.id

        async with db.user_lock(uid):
            removed = await db.remove_fish(uid, fish_id, quantity)
            if not removed:
                owned = await db.get_fish_qty(uid, fish_id)
                await interaction.response.send_message(
                    f"You only have **{owned}x {name}** — can't sell {quantity}.",
                    ephemeral=True,
                )
                return
            payout = value * quantity
            await db.add_balance(uid, payout)

        await interaction.response.send_message(
            f"💰 Sold **{quantity}x {emoji} {name}** for **{payout:,} {config.CURRENCY_NAME}**."
        )

    @sell.autocomplete("fish")
    async def sell_autocomplete(self, interaction: discord.Interaction, current: str):
        rows = {r["fish_id"]: r["quantity"] for r in await db.get_inventory(interaction.user.id)}
        options = []
        for fish_id, name, emoji, rarity, value, _ in gd.FISH:
            if fish_id in rows and current.lower() in name.lower():
                options.append(app_commands.Choice(name=f"{name} (x{rows[fish_id]})", value=name))
        return options[:25]

    @app_commands.command(name="sell-all", description="Sell every fish in your inventory (optionally filtered by rarity).")
    @app_commands.describe(rarity="Only sell this rarity (optional)")
    @app_commands.choices(rarity=[
        app_commands.Choice(name=r.title(), value=r) for r in gd.RARITY_ORDER
    ])
    async def sell_all(self, interaction: discord.Interaction, rarity: app_commands.Choice[str] = None):
        uid = interaction.user.id
        async with db.user_lock(uid):
            rows = await db.get_inventory(uid)
            total = 0
            count = 0
            for row in rows:
                f = gd.FISH_BY_ID[row["fish_id"]]
                _, name, emoji, r, value, _ = f
                if rarity and r != rarity.value:
                    continue
                qty = row["quantity"]
                await db.remove_fish(uid, row["fish_id"], qty)
                total += value * qty
                count += qty
            if total > 0:
                await db.add_balance(uid, total)

        if count == 0:
            await interaction.response.send_message("Nothing to sell.", ephemeral=True)
            return

        filt = f" ({rarity.value})" if rarity else ""
        await interaction.response.send_message(
            f"💰 Sold **{count}** fish{filt} for **{total:,} {config.CURRENCY_NAME}**."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Inventory(bot))
