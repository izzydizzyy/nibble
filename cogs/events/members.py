import discord
from discord.ext import commands

from utils.format import user_line
from utils.layout import LogLayout
from utils.views import IDButton


class MemberLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        dest = await self._channel_for(member.guild.id, "member_join")
        if dest is None:
            return
        age_days = (discord.utils.utcnow() - member.created_at).days
        view = LogLayout(
            emoji_key="member_join",
            title="Member Joined",
            color=self.bot.theme_color,
            thumbnail=member.display_avatar.url,
            fields=[
                ("Username", user_line(member)),
                ("Account Created", f"<t:{int(member.created_at.timestamp())}:R> ({age_days} days ago)"),
                ("Member Count", str(member.guild.member_count)),
            ],
            footer=f"User ID: {member.id}",
            buttons=[IDButton("User ID", member.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        dest = await self._channel_for(member.guild.id, "member_leave")
        if dest is None:
            return
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        view = LogLayout(
            emoji_key="member_leave",
            title="Member Left",
            color=self.bot.theme_color,
            thumbnail=member.display_avatar.url,
            fields=[
                ("Username", user_line(member)),
                ("Roles", ", ".join(roles) if roles else "*None*"),
                ("Member Count", str(member.guild.member_count)),
            ],
            footer=f"User ID: {member.id}",
            buttons=[IDButton("User ID", member.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild

        if before.nick != after.nick:
            dest = await self._channel_for(guild.id, "member_update")
            if dest:
                view = LogLayout(
                    emoji_key="member_update",
                    title="Nickname Changed",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(after)),
                        ("Before", before.nick or "*None*"),
                        ("After", after.nick or "*None*"),
                    ],
                    footer=f"User ID: {after.id}",
                    buttons=[IDButton("User ID", after.id)],
                )
                await dest.send(view=view)

        if before.roles != after.roles:
            dest = await self._channel_for(guild.id, "member_update")
            if dest:
                added = [r.mention for r in after.roles if r not in before.roles]
                removed = [r.mention for r in before.roles if r not in after.roles]
                fields = [("Member", user_line(after))]
                if added:
                    fields.append(("Roles Added", ", ".join(added)))
                if removed:
                    fields.append(("Roles Removed", ", ".join(removed)))
                if len(fields) > 1:
                    view = LogLayout(
                        emoji_key="member_update",
                        title="Member Roles Updated",
                        color=self.bot.theme_color,
                        fields=fields,
                        footer=f"User ID: {after.id}",
                        buttons=[IDButton("User ID", after.id)],
                    )
                    await dest.send(view=view)

        if before.timed_out_until != after.timed_out_until:
            dest = await self._channel_for(guild.id, "member_timeout")
            if dest:
                if after.timed_out_until:
                    title = "Member Timed Out"
                    fields = [
                        ("Member", user_line(after)),
                        ("Expires", f"<t:{int(after.timed_out_until.timestamp())}:R>"),
                    ]
                else:
                    title = "Timeout Removed"
                    fields = [("Member", user_line(after))]
                view = LogLayout(
                    emoji_key="member_timeout",
                    title=title,
                    color=self.bot.theme_color,
                    fields=fields,
                    footer=f"User ID: {after.id}",
                    buttons=[IDButton("User ID", after.id)],
                )
                await dest.send(view=view)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        for guild in self.bot.guilds:
            member = guild.get_member(after.id)
            if member is None:
                continue
            dest = await self._channel_for(guild.id, "username_update")
            if dest is None:
                continue
            if before.name != after.name or before.discriminator != after.discriminator:
                view = LogLayout(
                    emoji_key="username_update",
                    title="Username Changed",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(after)),
                        ("Before", str(before)),
                        ("After", str(after)),
                    ],
                    footer=f"User ID: {after.id}",
                    buttons=[IDButton("User ID", after.id)],
                )
                await dest.send(view=view)
            if before.avatar != after.avatar:
                view = LogLayout(
                    emoji_key="username_update",
                    title="Avatar Changed",
                    color=self.bot.theme_color,
                    thumbnail=after.display_avatar.url,
                    fields=[("Member", user_line(after))],
                    footer=f"User ID: {after.id}",
                    buttons=[IDButton("User ID", after.id)],
                )
                await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberLogs(bot))
