from __future__ import annotations

import discord

# Spotify-adjacent green, used as the one accent color everywhere.
# Every Replay surface uses this same accent so nothing looks like a
# random rainbow of embed colors.
ACCENT = discord.Color.from_rgb(30, 215, 96)


class StatRow:
    """One line of a stats block: 'label' on top (dim), value below (bold)."""

    def __init__(self, label: str, value: str):
        self.label = label
        self.value = value

    def render(self) -> str:
        return f"-# {self.label}\n**{self.value}**"


def header_text(title: str, subtitle: str | None = None) -> str:
    lines = [f"# {title}"]
    if subtitle:
        lines.append(f"-# {subtitle}")
    return "\n".join(lines)


def stat_block(rows: list[StatRow]) -> str:
    return "\n\n".join(row.render() for row in rows)


class ReplayContainer(discord.ui.Container):
    """Every Replay response is one of these: a single container with
    the same accent color, so the whole bot reads as one product."""

    def __init__(self, *children, accent: discord.Color = ACCENT):
        super().__init__(*children, accent_colour=accent)


class ReplayView(discord.ui.LayoutView):
    """Base LayoutView. Subclasses build one ReplayContainer in __init__
    and add it via add_item — kept this thin so every command's view
    stays a small, readable class instead of a wall of nested calls."""

    def __init__(self):
        super().__init__(timeout=180)


def action_row(*buttons: discord.ui.Button) -> discord.ui.ActionRow:
    row = discord.ui.ActionRow()
    for button in buttons:
        row.add_item(button)
    return row


def not_enough_data_view(context: str) -> ReplayView:
    view = ReplayView()
    container = ReplayContainer(
        discord.ui.TextDisplay(f"# not enough data yet\n-# {context}")
    )
    view.add_item(container)
    return view
