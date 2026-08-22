import discord
from discord.ext import commands

from utils.audit import find_actor
from utils.format import user_line
from utils.layout import LogLayout
from utils.views import IDButton


class ModerationLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        actor = await find_actor(member.guild, discord.AuditLogAction.kick, member.id)
        if actor is None:
            return
        dest = await self._channel_for(member.guild.id, "member_kick")
        if dest is None:
            return
        view = LogLayout(
            emoji_key="member_kick",
            title="Member Kicked",
            color=self.bot.theme_color,
            thumbnail=member.display_avatar.url,
            fields=[
                ("Username", user_line(member)),
                ("Kicked By", user_line(actor)),
            ],
            footer=f"User ID: {member.id}",
            buttons=[IDButton("User ID", member.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.abc.User):
        dest = await self._channel_for(guild.id, "member_ban")
        if dest is None:
            return
        actor = await find_actor(guild, discord.AuditLogAction.ban, user.id)
        reason = None
        if guild.me.guild_permissions.view_audit_log:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == user.id:
                    reason = entry.reason
                    break
        view = LogLayout(
            emoji_key="member_ban",
            title="Member Banned",
            color=self.bot.theme_color,
            thumbnail=user.display_avatar.url,
            fields=[
                ("Username", user_line(user)),
                ("Banned By", user_line(actor)),
                ("Reason", reason or "*No reason provided*"),
            ],
            footer=f"User ID: {user.id}",
            buttons=[IDButton("User ID", user.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.abc.User):
        dest = await self._channel_for(guild.id, "member_unban")
        if dest is None:
            return
        actor = await find_actor(guild, discord.AuditLogAction.unban, user.id)
        view = LogLayout(
            emoji_key="member_unban",
            title="Member Unbanned",
            color=self.bot.theme_color,
            thumbnail=user.display_avatar.url,
            fields=[
                ("Username", user_line(user)),
                ("Unbanned By", user_line(actor)),
            ],
            footer=f"User ID: {user.id}",
            buttons=[IDButton("User ID", user.id)],
        )
        await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationLogs(bot))
