import discord
from discord.ext import commands

from utils.layout import LogLayout
from utils.views import IDButton


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
        view = LogLayout(
            emoji_key="role_create",
            title="Role Created",
            color=self.bot.theme_color,
            fields=[
                ("Role", role.mention),
                ("Color", str(role.color)),
                ("Hoisted", str(role.hoist)),
            ],
            footer=f"Role ID: {role.id}",
            buttons=[IDButton("Role ID", role.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        dest = await self._channel_for(role.guild.id, "role_delete")
        if dest is None:
            return
        view = LogLayout(
            emoji_key="role_delete",
            title="Role Deleted",
            color=self.bot.theme_color,
            fields=[("Name", f"@{role.name}")],
            footer=f"Role ID: {role.id}",
            buttons=[IDButton("Role ID", role.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        dest = await self._channel_for(after.guild.id, "role_update")
        if dest is None:
            return
        changes = []
        if before.name != after.name:
            changes.append(("Name", f"{before.name} -> {after.name}"))
        if before.color != after.color:
            changes.append(("Color", f"{before.color} -> {after.color}"))
        if before.permissions != after.permissions:
            changes.append(("Permissions", "Changed (see audit log for detail)"))
        if not changes:
            return
        view = LogLayout(
            emoji_key="role_update",
            title="Role Updated",
            color=self.bot.theme_color,
            fields=[("Role", after.mention)] + changes,
            footer=f"Role ID: {after.id}",
            buttons=[IDButton("Role ID", after.id)],
        )
        await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleLogs(bot))
