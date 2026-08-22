"""
Small, focused button rows attached to log embeds. Each button either
reveals an ID (ephemeral, so it doesn't clutter the log channel) or links
straight to the relevant object.
"""

import discord


class IDButton(discord.ui.Button):
    def __init__(self, label: str, object_id: int, emoji: str | None = None):
        super().__init__(
            label=label, style=discord.ButtonStyle.secondary, emoji=emoji
        )
        self.object_id = object_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"`{self.object_id}`", ephemeral=True
        )


class JumpButton(discord.ui.Button):
    def __init__(self, label: str, url: str, emoji: str | None = None):
        super().__init__(
            label=label, style=discord.ButtonStyle.link, url=url, emoji=emoji
        )


class LogView(discord.ui.View):
    """
    Build with a fluent-ish helper so cogs don't repeat boilerplate:

        view = LogView().add_id("Message ID", message.id).add_jump("Jump", url)
    """

    def __init__(self):
        super().__init__(timeout=None)

    def add_id(self, label: str, object_id: int, emoji: str | None = None) -> "LogView":
        self.add_item(IDButton(label, object_id, emoji))
        return self

    def add_jump(self, label: str, url: str, emoji: str | None = None) -> "LogView":
        self.add_item(JumpButton(label, url, emoji))
        return self
