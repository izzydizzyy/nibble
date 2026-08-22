import discord
from discord.ext import commands

from utils.embeds import log_embed
from utils.views import LogView


class ChannelLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        dest = await self._channel_for(channel.guild.id, "channel_create")
        if dest is None:
            return
        embed = log_embed(
            title="Channel Created",
            color=self.bot.theme_color,
            fields=[
                ("Name", channel.mention, False),
                ("Type", str(channel.type).replace("_", " ").title(), False),
                ("Category", channel.category.name if channel.category else "*None*", False),
            ],
            footer=f"Channel ID: {channel.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Channel ID", channel.id))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        dest = await self._channel_for(channel.guild.id, "channel_delete")
        if dest is None:
            return
        embed = log_embed(
            title="Channel Deleted",
            color=self.bot.theme_color,
            fields=[
                ("Name", f"#{channel.name}", False),
                ("Type", str(channel.type).replace("_", " ").title(), False),
                ("Category", channel.category.name if channel.category else "*None*", False),
            ],
            footer=f"Channel ID: {channel.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Channel ID", channel.id))

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        dest = await self._channel_for(after.guild.id, "channel_update")
        if dest is None:
            return
        changes = []
        if before.name != after.name:
            changes.append(("Name", f"{before.name} -> {after.name}", False))
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                changes.append(("Topic", f"{before.topic or '*None*'} -> {after.topic or '*None*'}", False))
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(
                    ("Slowmode", f"{before.slowmode_delay}s -> {after.slowmode_delay}s", False)
                )
        if not changes:
            return
        embed = log_embed(
            title="Channel Updated",
            color=self.bot.theme_color,
            fields=[("Channel", after.mention, False)] + changes,
            footer=f"Channel ID: {after.id}",
        )
        await dest.send(embed=embed, view=LogView().add_id("Channel ID", after.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelLogs(bot))
