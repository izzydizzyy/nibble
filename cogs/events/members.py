import discord
from discord.ext import commands

from utils.embeds import log_embed, user_line
from utils.views import LogView


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
        embed = log_embed(
            title="Member Joined",
            color=self.bot.theme_color,
            fields=[
                ("Username", user_line(member), False),
                ("Account Created", f"<t:{int(member.created_at.timestamp())}:R>", True),
                ("Account Age", f"{age_days} days", True),
                ("Member Count", str(member.guild.member_count), False),
            ],
            thumbnail=member.display_avatar.url,
            footer=f"User ID: {member.id}",
        )
        view = LogView().add_id("User ID", member.id)
        await dest.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        dest = await self._channel_for(member.guild.id, "member_leave")
        if dest is None:
            return
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        embed = log_embed(
            title="Member Left",
            color=self.bot.theme_color,
            fields=[
                ("Username", user_line(member), False),
                ("Roles", ", ".join(roles) if roles else "*None*", False),
                ("Member Count", str(member.guild.member_count), False),
            ],
            thumbnail=member.display_avatar.url,
            footer=f"User ID: {member.id}",
        )
        view = LogView().add_id("User ID", member.id)
        await dest.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild

        if before.nick != after.nick:
            dest = await self._channel_for(guild.id, "member_update")
            if dest:
                embed = log_embed(
                    title="Nickname Changed",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(after), False),
                        ("Before", before.nick or "*None*", True),
                        ("After", after.nick or "*None*", True),
                    ],
                    footer=f"User ID: {after.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", after.id))

        if before.roles != after.roles:
            dest = await self._channel_for(guild.id, "member_update")
            if dest:
                added = [r.mention for r in after.roles if r not in before.roles]
                removed = [r.mention for r in before.roles if r not in after.roles]
                fields = [("Member", user_line(after), False)]
                if added:
                    fields.append(("Roles Added", ", ".join(added), False))
                if removed:
                    fields.append(("Roles Removed", ", ".join(removed), False))
                if len(fields) > 1:
                    embed = log_embed(
                        title="Member Roles Updated",
                        color=self.bot.theme_color,
                        fields=fields,
                        footer=f"User ID: {after.id}",
                    )
                    await dest.send(embed=embed, view=LogView().add_id("User ID", after.id))

        if before.timed_out_until != after.timed_out_until:
            dest = await self._channel_for(guild.id, "member_timeout")
            if dest:
                if after.timed_out_until:
                    fields = [
                        ("Member", user_line(after), False),
                        (
                            "Expires",
                            f"<t:{int(after.timed_out_until.timestamp())}:R>",
                            False,
                        ),
                    ]
                    title = "Member Timed Out"
                else:
                    fields = [("Member", user_line(after), False)]
                    title = "Timeout Removed"
                embed = log_embed(
                    title=title,
                    color=self.bot.theme_color,
                    fields=fields,
                    footer=f"User ID: {after.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", after.id))

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
                embed = log_embed(
                    title="Username Changed",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(after), False),
                        ("Before", str(before), True),
                        ("After", str(after), True),
                    ],
                    footer=f"User ID: {after.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", after.id))
            if before.avatar != after.avatar:
                embed = log_embed(
                    title="Avatar Changed",
                    color=self.bot.theme_color,
                    fields=[("Member", user_line(after), False)],
                    thumbnail=after.display_avatar.url,
                    footer=f"User ID: {after.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", after.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberLogs(bot))
