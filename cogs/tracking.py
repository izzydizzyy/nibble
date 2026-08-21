from __future__ import annotations

import logging

import discord
from discord.ext import commands

log = logging.getLogger("replay.tracking")


class Tracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.bot.guild_repo.ensure_guild(guild.id, guild.name)
        log.info("joined guild: %s (%d)", guild.name, guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        await self.bot.guild_repo.ensure_member(member.guild.id, member.id)
        await self.bot.user_repo.upsert(member.id, str(member), member.display_avatar.key)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        settings = await self.bot.get_guild_settings(message.guild.id)
        if not settings.get("track_messages", True):
            return
        if await self.bot.guild_repo.is_opted_out(message.guild.id, message.author.id):
            return
        await self.bot.guild_repo.ensure_member(message.guild.id, message.author.id)
        await self.bot.message_tracker.on_message(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None or payload.member is None or payload.member.bot:
            return
        settings = await self.bot.get_guild_settings(payload.guild_id)
        if not settings.get("track_messages", True):
            return
        if await self.bot.guild_repo.is_opted_out(payload.guild_id, payload.user_id):
            return
        await self.bot.reaction_tracker.on_raw_reaction_add(payload)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        if member.bot:
            return
        if await self.bot.guild_repo.is_opted_out(member.guild.id, member.id):
            return
        await self.bot.guild_repo.ensure_member(member.guild.id, member.id)
        await self.bot.voice_tracker.on_voice_state_update(member, before, after)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.bot or after.guild is None:
            return
        settings = await self.bot.get_guild_settings(after.guild.id)
        if not settings.get("track_presence", True):
            return
        if await self.bot.guild_repo.is_opted_out(after.guild.id, after.id):
            return
        await self.bot.presence_tracker.on_presence_update(before, after)


async def setup(bot):
    await bot.add_cog(Tracking(bot))
