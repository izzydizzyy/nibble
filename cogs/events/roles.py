import discord
from discord.ext import commands

from utils.embeds import log_embed
from utils.views import LogView


class RoleLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        dest = await self._channel_for(role.guild.id, "role_create")
        if dest is None:
            return
        embed = log_embed(
            title="Role Created",
            color=self.bot.theme_color,
            fields=[
                ("Role", role.mention, False),
                ("Color", str(role.color), True),
                ("Hoisted", str(role.hoist), True),
            ],
            footer=f"Role ID: {role.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Role ID", role.id))

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        dest = await self._channel_for(role.guild.id, "role_delete")
        if dest is None:
            return
        embed = log_embed(
            title="Role Deleted",
            color=self.bot.theme_color,
            fields=[("Name", f"@{role.name}", False)],
            footer=f"Role ID: {role.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Role ID", role.id))

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        dest = await self._channel_for(after.guild.id, "role_update")
        if dest is None:
            return
        changes = []
        if before.name != after.name:
            changes.append(("Name", f"{before.name} -> {after.name}", False))
        if before.color != after.color:
            changes.append(("Color", f"{before.color} -> {after.color}", False))
        if before.permissions != after.permissions:
            changes.append(("Permissions", "Changed (see audit log for detail)", False))
        if not changes:
            return
        embed = log_embed(
            title="Role Updated",
            color=self.bot.theme_color,
            fields=[("Role", after.mention, False)] + changes,
            footer=f"Role ID: {after.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Role ID", after.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleLogs(bot))
