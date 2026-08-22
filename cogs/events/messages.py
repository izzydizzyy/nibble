import discord
from discord.ext import commands

from utils.format import trim, user_line, channel_line
from utils.layout import LogLayout
from utils.views import IDButton, JumpButton


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

        fields = [
            ("Author", user_line(message.author)),
            ("Channel", channel_line(message.channel)),
            ("Content", trim(message.content)),
        ]
        if message.attachments:
            fields.append(("Attachments", "\n".join(a.url for a in message.attachments[:5])))

        view = LogLayout(
            emoji_key="message_delete",
            title="Message Deleted",
            color=self.bot.theme_color,
            fields=fields,
            footer=f"Message ID: {message.id}",
            buttons=[IDButton("Message ID", message.id)],
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if not messages or messages[0].guild is None:
            return
        view = LogLayout(
            emoji_key="message_bulk_delete",
            title="Bulk Message Delete",
            color=self.bot.theme_color,
            fields=[
                ("Channel", channel_line(messages[0].channel)),
                ("Messages Removed", str(len(messages))),
            ],
            footer=f"Channel ID: {messages[0].channel.id}",
        )
        dest = await self._channel_for(messages[0].guild.id, "message_bulk_delete")
        if dest is None:
            return
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None or (before.author and before.author.bot):
            return
        if before.content == after.content:
            return
        dest = await self._channel_for(before.guild.id, "message_edit")
        if dest is None:
            return

        view = LogLayout(
            emoji_key="message_edit",
            title="Message Edited",
            color=self.bot.theme_color,
            fields=[
                ("Author", user_line(before.author)),
                ("Channel", channel_line(before.channel)),
                ("Before", trim(before.content)),
                ("After", trim(after.content)),
            ],
            footer=f"Message ID: {before.id}",
            buttons=[
                IDButton("Message ID", before.id),
                JumpButton("Jump to Message", after.jump_url),
            ],
        )
        await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageLogs(bot))
