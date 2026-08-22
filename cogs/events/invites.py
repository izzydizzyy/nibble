import discord
from discord.ext import commands

from utils.embeds import log_embed, user_line
from utils.views import LogView


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
        embed = log_embed(
            title="Invite Created",
            color=self.bot.theme_color,
            fields=[
                ("Code", f"`{invite.code}`", True),
                ("Channel", invite.channel.mention, True),
                ("Created By", user_line(invite.inviter), False),
                (
                    "Expires",
                    f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Never",
                    False,
                ),
            ],
            footer=f"Max Uses: {invite.max_uses or 'Unlimited'}",
        )
        await dest.send(embed=embed, view=LogView().add_jump("Open Channel", invite.channel.jump_url))

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        dest = await self._channel_for(invite.guild.id, "invite_delete")
        if dest is None:
            return
        embed = log_embed(
            title="Invite Deleted",
            color=self.bot.theme_color,
            fields=[
                ("Code", f"`{invite.code}`", True),
                ("Channel", invite.channel.mention if invite.channel else "Unknown", True),
            ],
        )
        await dest.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(InviteLogs(bot))
