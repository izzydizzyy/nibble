"""
Custom Nibble emoji IDs, uploaded as application emojis (Developer Portal ->
your app -> Emojis), so they render in any server the bot is in without
needing to be uploaded per-guild.

If you add/remove/rename emojis in the dashboard, update the IDs here to
match. Discord emoji syntax is <:name:id> for static, <a:name:id> for
animated -- these are all static.
"""

NIBBLE_LOVE = "<:nibble_love:1540226858522648656>"
NIBBLE_DAB = "<:nibble_dab:1540226857893494794>"
NIBBLE_UWU = "<:nibble_uwu:1540226856962498590>"
NIBBLE_CRY = "<:nibble_cry:1540226856207253555>"
NIBBLE_HYPE = "<:nibble_hype:1540226833004625930>"
NIBBLE_LOL = "<:nibble_lol:1540226832215842886>"
NIBBLE_ANGRY = "<:nibble_angry:1540226831557599322>"
NIBBLE_EATFISH = "<:nibble_eatfish:1540226830450294837>"
NIBBLE_PAT = "<:nibble_pat:1540226830005575741>"
NIBBLE_GAME = "<:nibble_game:1540226829305253908>"

# Raw numeric IDs for the same emojis, used to build CDN thumbnail URLs
# (https://cdn.discordapp.com/emojis/<id>.png) for Components V2 Thumbnail
# accessories -- those need an image URL, not the <:name:id> mention string.
NIBBLE_LOVE_ID = "1540226858522648656"
NIBBLE_DAB_ID = "1540226857893494794"
NIBBLE_UWU_ID = "1540226856962498590"
NIBBLE_CRY_ID = "1540226856207253555"
NIBBLE_HYPE_ID = "1540226833004625930"
NIBBLE_LOL_ID = "1540226832215842886"
NIBBLE_ANGRY_ID = "1540226831557599322"
NIBBLE_EATFISH_ID = "1540226830450294837"
NIBBLE_PAT_ID = "1540226830005575741"
NIBBLE_GAME_ID = "1540226829305253908"


def emoji_cdn_url(emoji_id: str) -> str:
    return f"https://cdn.discordapp.com/emojis/{emoji_id}.png"


# Nibble's reaction to your catch, keyed by rarity -- this is what makes a
# rare pull feel like an event instead of a bigger number. Ordered from
# "whatever" (common) to "losing his mind" (top rarity).
RARITY_REACTIONS = {
    "common": NIBBLE_GAME,
    "uncommon": NIBBLE_EATFISH,
    "rare": NIBBLE_LOL,
    "epic": NIBBLE_HYPE,
    "legendary": NIBBLE_UWU,
    "mythic": NIBBLE_DAB,
    "ancient": NIBBLE_LOVE,
}

RARITY_REACTION_IDS = {
    "common": NIBBLE_GAME_ID,
    "uncommon": NIBBLE_EATFISH_ID,
    "rare": NIBBLE_LOL_ID,
    "epic": NIBBLE_HYPE_ID,
    "legendary": NIBBLE_UWU_ID,
    "mythic": NIBBLE_DAB_ID,
    "ancient": NIBBLE_LOVE_ID,
}

# Used when a sell/spend fails, an empty inventory, etc.
EMPTY_REACTION = NIBBLE_CRY
