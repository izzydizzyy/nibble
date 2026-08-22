"""
Single source of truth for every emoji the bot displays.

These default to Unicode so the bot works immediately with zero setup.
To use custom emoji.gg art instead:

  1. Pick emojis from https://emoji.gg -- the "Mod", "Shield", and "Ban"
     categories fit a logging bot well.
  2. Upload each one to YOUR server (Server Settings -> Emoji -> Upload).
     Custom emojis only get a usable ID once they live in a server your
     bot can see -- emoji.gg itself doesn't hand out IDs, since the art
     is just an image file until you upload it somewhere.
  3. Replace the value below with the real string Discord gives you:
     "<:name:123456789012345678>" (or "<a:name:id>" if it's animated).

Nothing else in the codebase needs to change -- every cog pulls from
this dict by key.
"""

EMOJIS: dict[str, str] = {
    # messages
    "message_delete": "\U0001F5D1",   # wastebasket
    "message_edit": "\U0000270F",     # pencil
    "message_bulk_delete": "\U0001F9F9",  # broom
    # members
    "member_join": "\U0001F4E5",      # inbox tray
    "member_leave": "\U0001F4E4",     # outbox tray
    "member_update": "\U0001F3F7",    # label
    "username_update": "\U0001FAAA",  # id card
    # moderation
    "member_kick": "\U0001F462",      # boot
    "member_ban": "\U0001F528",       # hammer
    "member_unban": "\U0001F513",     # unlocked
    "member_timeout": "\U000023F1",   # stopwatch
    # channels
    "channel_create": "\U00002795",   # plus
    "channel_delete": "\U00002796",   # minus
    "channel_update": "\U0001F527",   # wrench
    # roles
    "role_create": "\U0001F3AD",      # masks
    "role_delete": "\U0001F3AD",
    "role_update": "\U0001F3AD",
    # voice
    "voice_join": "\U0001F50A",       # speaker high
    "voice_leave": "\U0001F507",      # muted speaker
    "voice_move": "\U0001F500",       # shuffle
    # server
    "invite_create": "\U0001F517",    # link
    "invite_delete": "\U0001F517",
    "emoji_update": "\U0001F600",     # grinning face
    "guild_update": "\U00002699",     # gear
    # ui
    "settings": "\U0001F6E0",         # hammer and wrench
    "vote": "\U0001F5F3",             # ballot box
    "help": "\U00002753",             # question mark
    "success": "\U00002705",          # check mark
    "error": "\U000026A0",            # warning
}
