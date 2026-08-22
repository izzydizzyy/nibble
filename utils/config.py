"""Static config values. Nothing server-specific lives here -- that's in the DB."""

import discord

THEME_COLOR = discord.Color(0xCBCB43)
ERROR_COLOR = discord.Color(0xE84F4F)
SUCCESS_COLOR = discord.Color(0x4FE87C)

VOTE_URL = "https://top.gg/"  # placeholder -- swap once the listing is live

# Every loggable event, grouped the way the /settings UI presents them.
EVENT_GROUPS: dict[str, dict[str, str]] = {
    "messages": {
        "message_delete": "Message Deleted",
        "message_edit": "Message Edited",
        "message_bulk_delete": "Bulk Message Delete",
    },
    "members": {
        "member_join": "Member Joined",
        "member_leave": "Member Left",
        "member_update": "Member Updated (nickname, roles, timeout)",
        "username_update": "Username / Avatar Changed",
    },
    "moderation": {
        "member_kick": "Member Kicked",
        "member_ban": "Member Banned",
        "member_unban": "Member Unbanned",
        "member_timeout": "Member Timed Out",
    },
    "channels": {
        "channel_create": "Channel Created",
        "channel_delete": "Channel Deleted",
        "channel_update": "Channel Updated",
    },
    "roles": {
        "role_create": "Role Created",
        "role_delete": "Role Deleted",
        "role_update": "Role Updated",
    },
    "voice": {
        "voice_join": "Voice Channel Joined",
        "voice_leave": "Voice Channel Left",
        "voice_move": "Voice Channel Switched",
    },
    "server": {
        "invite_create": "Invite Created",
        "invite_delete": "Invite Deleted",
        "emoji_update": "Emoji / Sticker Updated",
        "guild_update": "Server Settings Updated",
    },
}


def all_event_keys() -> list[str]:
    keys = []
    for group in EVENT_GROUPS.values():
        keys.extend(group.keys())
    return keys
