import discord
from discord.ext import commands

from utils.layout import LogLayout


class ServerLogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _channel_for(self, guild_id: int, event_key: str):
        channel_id = await self.bot.db.resolve_log_channel(guild_id, event_key)
        if not channel_id:
            return None
        return self.bot.get_channel(channel_id)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before, after):
        dest = await self._channel_for(guild.id, "emoji_update")
        if dest is None:
            return
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        fields = []
        if added:
            fields.append(("Added", " ".join(str(e) for e in added)))
        if removed:
            fields.append(("Removed", ", ".join(e.name for e in removed)))
        if not fields:
            return
        view = LogLayout(
            emoji_key="emoji_update",
            title="Emoji List Updated",
            color=self.bot.theme_color,
            fields=fields,
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before, after):
        dest = await self._channel_for(guild.id, "emoji_update")
        if dest is None:
            return
        added = [s for s in after if s not in before]
        removed = [s for s in before if s not in after]
        fields = []
        if added:
            fields.append(("Stickers Added", ", ".join(s.name for s in added)))
        if removed:
            fields.append(("Stickers Removed", ", ".join(s.name for s in removed)))
        if not fields:
            return
        view = LogLayout(
            emoji_key="emoji_update",
            title="Sticker List Updated",
            color=self.bot.theme_color,
            fields=fields,
        )
        await dest.send(view=view)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        dest = await self._channel_for(after.id, "guild_update")
        if dest is None:
            return
        changes = []
        if before.name != after.name:
            changes.append(("Name", f"{before.name} -> {after.name}"))
        if before.icon != after.icon:
            changes.append(("Icon", "Changed"))
        if before.owner_id != after.owner_id:
            changes.append(("Owner", f"<@{before.owner_id}> -> <@{after.owner_id}>"))
        if not changes:
            return
        view = LogLayout(
            emoji_key="guild_update",
            title="Server Settings Updated",
            color=self.bot.theme_color,
            fields=changes,
        )
        await dest.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerLogs(bot))
