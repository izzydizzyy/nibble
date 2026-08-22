import discord
from discord.ext import commands

from utils.embeds import log_embed, trim, user_line, channel_line
from utils.views import LogView


class MessageLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None or (message.author and message.author.bot):
            return
        dest = await self._channel_for(message.guild.id, "message_delete")
        if dest is None:
            return

        embed = log_embed(
            title="Message Deleted",
            color=self.bot.theme_color,
            fields=[
                ("Author", user_line(message.author), False),
                ("Channel", channel_line(message.channel), False),
                ("Content", trim(message.content), False),
            ],
            footer=f"Message ID: {message.id}",
        )
        if message.attachments:
            embed.add_field(
                name="Attachments",
                value="\n".join(a.url for a in message.attachments[:5]),
                inline=False,
            )

        view = LogView().add_id("Message ID", message.id)
        await dest.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages or messages[0].guild is None:
            return
        guild = messages[0].guild
        dest = await self._channel_for(guild.id, "message_bulk_delete")
        if dest is None:
            return

        embed = log_embed(
            title="Bulk Message Delete",
            color=self.bot.theme_color,
            fields=[
                ("Channel", channel_line(messages[0].channel), False),
                ("Messages Removed", str(len(messages)), False),
            ],
            footer=f"Channel ID: {messages[0].channel.id}",
        )
        await dest.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None or (before.author and before.author.bot):
            return
        if before.content == after.content:
            return
        dest = await self._channel_for(before.guild.id, "message_edit")
        if dest is None:
            return

        embed = log_embed(
            title="Message Edited",
            color=self.bot.theme_color,
            fields=[
                ("Author", user_line(before.author), False),
                ("Channel", channel_line(before.channel), False),
                ("Before", trim(before.content), False),
                ("After", trim(after.content), False),
            ],
            footer=f"Message ID: {before.id}",
        )
        view = LogView().add_id("Message ID", before.id).add_jump("Jump to Message", after.jump_url)
        await dest.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLogs(bot))
