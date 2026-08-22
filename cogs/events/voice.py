import discord
from discord.ext import commands

from utils.format import user_line
from utils.layout import LogLayout
from utils.views import IDButton


class VoiceLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if before.channel == after.channel:
            return

        if before.channel is None and after.channel is not None:
            dest = await self._channel_for(member.guild.id, "voice_join")
            if dest:
                view = LogLayout(
                    emoji_key="voice_join",
                    title="Voice Channel Joined",
                    color=self.bot.theme_color,
                    fields=[("Member", user_line(member)), ("Channel", after.channel.mention)],
                    footer=f"User ID: {member.id}",
                    buttons=[IDButton("User ID", member.id)],
                )
                await dest.send(view=view)

        elif before.channel is not None and after.channel is None:
            dest = await self._channel_for(member.guild.id, "voice_leave")
            if dest:
                view = LogLayout(
                    emoji_key="voice_leave",
                    title="Voice Channel Left",
                    color=self.bot.theme_color,
                    fields=[("Member", user_line(member)), ("Channel", before.channel.mention)],
                    footer=f"User ID: {member.id}",
                    buttons=[IDButton("User ID", member.id)],
                )
                await dest.send(view=view)

        else:
            dest = await self._channel_for(member.guild.id, "voice_move")
            if dest:
                view = LogLayout(
                    emoji_key="voice_move",
                    title="Voice Channel Switched",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(member)),
                        ("From", before.channel.mention),
                        ("To", after.channel.mention),
                    ],
                    footer=f"User ID: {member.id}",
                    buttons=[IDButton("User ID", member.id)],
                )
                await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLogs(bot))
