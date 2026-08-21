from __future__ import annotations

import discord

from database.repositories.reactions import ReactionRepository


def emoji_key(emoji: discord.PartialEmoji | discord.Emoji | str) -> str:
    if isinstance(emoji, str):
        return emoji
    if emoji.id is None:
        return str(emoji.name)
    return f"{emoji.name}:{emoji.id}"


class ReactionTracker:
    def __init__(self, repo: ReactionRepository):
        self.repo = repo

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None or payload.member is None or payload.member.bot:
            return
        await self.repo.record(payload.guild_id, payload.user_id, emoji_key(payload.emoji))
