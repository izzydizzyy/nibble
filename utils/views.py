"""
Plain discord.ui.Button subclasses. These get passed into LogLayout's
`buttons=` list and end up inside a CV2 ui.ActionRow -- the button
class itself doesn't change between legacy views and CV2, only where
it's mounted.
"""

import discord


class IDButton(discord.ui.Button):
    def __init__(self, label: str, object_id: int, emoji: str | None = None):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
        self.object_id = object_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"`{self.object_id}`", ephemeral=True)


class JumpButton(discord.ui.Button):
    def __init__(self, label: str, url: str, emoji: str | None = None):
        super().__init__(label=label, style=discord.ButtonStyle.link, url=url, emoji=emoji)
