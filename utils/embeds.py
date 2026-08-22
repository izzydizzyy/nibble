"""
One builder, used by every event listener, so every log entry looks like it
came from the same bot instead of a patchwork of ad-hoc embeds.
"""

from __future__ import annotations

import discord

from utils.config import THEME_COLOR


def log_embed(
    *,
    title: str,
    fields: list[tuple[str, str, bool]],
    color: discord.Color = THEME_COLOR,
    description: str | None = None,
    thumbnail: str | None = None,
    footer: str | None = None,
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    embed.timestamp = discord.utils.utcnow()
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    return embed


def trim(text: str | None, limit: int = 1000) -> str:
    if not text:
        return "*None*"
    text = text.replace("```", "'''")
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def user_line(user: discord.abc.User | None) -> str:
    if user is None:
        return "Unknown"
    return f"{user.mention} (`{user.id}`)"


def channel_line(channel) -> str:
    if channel is None:
        return "Unknown"
    return f"{channel.mention} (`{channel.id}`)"
