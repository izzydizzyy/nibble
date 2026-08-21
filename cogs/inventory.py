import discord
from discord import app_commands
from discord.ext import commands

import database as db
import game_data as gd
import utils.ui as ui


class Inventory(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="See the fish you're holding.")
    async def inventory(self, interaction: discord.Interaction):
        rows = await db.get_inventory(interaction.user.id)
        await interaction.response.send_message(
            view=ui.inventory_view(target=interaction.user, rows=rows)
        )

    @app_commands.command(name="collection", description="See your collection progress across all species.")
    async def collection(self, interaction: discord.Interaction):
        rows = await db.get_inventory(interaction.user.id)
        owned_ids = {r["fish_id"] for r in rows}
        await interaction.response.send_message(
            view=ui.collection_view(
                target=interaction.user,
                owned_ids=owned_ids,
                total_species=len(gd.FISH),
            )
        )

    @app_commands.command(name="sell", description="Sell fish from your inventory.")
    @app_commands.describe(fish="Name of the fish to sell", quantity="How many to sell (default 1)")
    async def sell(self, interaction: discord.Interaction, fish: str, quantity: int = 1):
        if quantity < 1:
            await interaction.response.send_message(
                view=ui.error_view("Quantity must be at least 1."), ephemeral=True
            )
            return

        match = next((f for f in gd.FISH if f[1].lower() == fish.lower()), None)
        if not match:
            await interaction.response.send_message(
                view=ui.error_view(f"Couldn't find a fish named **{fish}**. Check `/inventory` for exact names."),
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
                    view=ui.error_view(f"You only have **{owned}x {name}** — can't sell {quantity}."),
                    ephemeral=True,
                )
                return
            payout = value * quantity
            await db.add_balance(uid, payout)

        await interaction.response.send_message(
            view=ui.sell_view(name=name, emoji=emoji, quantity=quantity, payout=payout)
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
            await interaction.response.send_message(
                view=ui.error_view("Nothing to sell."), ephemeral=True
            )
            return

        await interaction.response.send_message(
            view=ui.sell_all_view(
                count=count, total=total,
                rarity_filter=rarity.value if rarity else None,
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Inventory(bot))
