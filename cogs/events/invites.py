import discord
from discord.ext import commands

from utils.format import user_line
from utils.layout import LogLayout
from utils.views import JumpButton


class InviteLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        dest = await self._channel_for(invite.guild.id, "invite_create")
        if dest is None:
            return
        expires = f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Never"
        view = LogLayout(
            emoji_key="invite_create",
            title="Invite Created",
            color=self.bot.theme_color,
            fields=[
                ("Code", f"`{invite.code}`"),
                ("Channel", invite.channel.mention),
                ("Created By", user_line(invite.inviter)),
                ("Expires", expires),
            ],
            footer=f"Max Uses: {invite.max_uses or 'Unlimited'}",
            buttons=[JumpButton("Open Channel", invite.channel.jump_url)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        dest = await self._channel_for(invite.guild.id, "invite_delete")
        if dest is None:
            return
        view = LogLayout(
            emoji_key="invite_delete",
            title="Invite Deleted",
            color=self.bot.theme_color,
            fields=[
                ("Code", f"`{invite.code}`"),
                ("Channel", invite.channel.mention if invite.channel else "Unknown"),
            ],
        )
        await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(InviteLogs(bot))
