"""
Every log message in this bot is a real Components V2 layout: a
LayoutView wrapping a single Container, built from TextDisplay /
Section / Separator / ActionRow. No discord.Embed anywhere -- Discord
doesn't allow mixing embeds with CV2 in the same message, and CV2 is
what the theme color, dividers, and inline buttons actually need.

Usage from a cog:

    view = LogLayout(
        emoji_key="message_delete",
        title="Message Deleted",
        color=bot.theme_color,
        fields=[("Author", user_line(msg.author)), ("Channel", channel_line(msg.channel))],
        footer=f"Message ID: {msg.id}",
        buttons=[IDButton("Message ID", msg.id)],
    )
    await dest.send(view=view)
"""

from __future__ import annotations

import discord
from discord import ui

from utils.emojis import EMOJIS


class LogLayout(ui.LayoutView):
    def __init__(
        self,
        *,
        title: str,
        fields: list[tuple[str, str]],
        color: discord.Color,
        emoji_key: str | None = None,
        description: str | None = None,
        thumbnail: str | None = None,
        footer: str | None = None,
        buttons: list[ui.Button] | None = None,
    ):
        super().__init__(timeout=None)

        emoji = EMOJIS.get(emoji_key, "") if emoji_key else ""
        heading = f"{emoji}  **{title}**".strip()

        children: list[ui.Item] = []

        if thumbnail:
            children.append(ui.Section(heading, accessory=ui.Thumbnail(thumbnail)))
        else:
            children.append(ui.TextDisplay(heading))

        if description:
            children.append(ui.TextDisplay(description))

        if fields:
            children.append(ui.Separator())
            for label, value in fields:
                children.append(ui.TextDisplay(f"**{label}**\n{value}"))

        if footer:
            children.append(ui.Separator())
            timestamp = discord.utils.format_dt(discord.utils.utcnow(), style="f")
            children.append(ui.TextDisplay(f"-# {footer}  --  {timestamp}"))

        if buttons:
            children.append(ui.ActionRow(*buttons))

        self.add_item(ui.Container(*children, accent_color=color))
