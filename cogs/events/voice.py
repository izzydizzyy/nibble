import discord
from discord.ext import commands

from utils.embeds import log_embed, user_line
from utils.views import LogView


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
                embed = log_embed(
                    title="Voice Channel Joined",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(member), False),
                        ("Channel", after.channel.mention, False),
                    ],
                    footer=f"User ID: {member.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", member.id))

        elif before.channel is not None and after.channel is None:
            dest = await self._channel_for(member.guild.id, "voice_leave")
            if dest:
                embed = log_embed(
                    title="Voice Channel Left",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(member), False),
                        ("Channel", before.channel.mention, False),
                    ],
                    footer=f"User ID: {member.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", member.id))

        else:
            dest = await self._channel_for(member.guild.id, "voice_move")
            if dest:
                embed = log_embed(
                    title="Voice Channel Switched",
                    color=self.bot.theme_color,
                    fields=[
                        ("Member", user_line(member), False),
                        ("From", before.channel.mention, True),
                        ("To", after.channel.mention, True),
                    ],
                    footer=f"User ID: {member.id}",
                )
                await dest.send(embed=embed, view=LogView().add_id("User ID", member.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLogs(bot))
