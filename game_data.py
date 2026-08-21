"""
Static game-balance data. This is the file you edit to add new fish,
adjust rarity odds, or add new rods. Nothing here touches the DB.
"""

# Rarity tiers: name -> weight (odds), accent color, and a small label
# emoji (only used in list-style views like /collection -- catch results
# lean on the container's accent color instead of a bullet emoji).
RARITIES = {
    "common":    {"weight": 550, "color": 0x9AA0A6, "emoji": "⚪"},
    "uncommon":  {"weight": 250, "color": 0x57F287, "emoji": "🟢"},
    "rare":      {"weight": 120, "color": 0x4C9AFF, "emoji": "🔵"},
    "epic":      {"weight": 50,  "color": 0xA855F7, "emoji": "🟣"},
    "legendary": {"weight": 20,  "color": 0xE89A4A, "emoji": "🟠"},
    "mythic":    {"weight": 8,   "color": 0xFF4D8D, "emoji": "🔴"},
    "ancient":   {"weight": 2,   "color": 0xFDC330, "emoji": "🟡"},
}

# Cosmetic weight/size range shown on a catch, in lbs -- flavor only, not
# stored or persisted. Bigger and more varied at higher rarities.
WEIGHT_RANGES = {
    "common":    (0.4, 2.0),
    "uncommon":  (1.0, 4.0),
    "rare":      (3.0, 9.0),
    "epic":      (6.0, 16.0),
    "legendary": (12.0, 32.0),
    "mythic":    (25.0, 65.0),
    "ancient":   (50.0, 130.0),
}

# Rods gate which rarities you can even roll, and shift the odds toward rarer
# fish. min_rod_tier on a fish species below refers to the "tier" field here.
RODS = {
    1: {"name": "Twig Rod",       "price": 0,      "max_rarity": "uncommon",
        "rarity_bonus": 0},
    2: {"name": "Oak Rod",        "price": 750,    "max_rarity": "rare",
        "rarity_bonus": 5},
    3: {"name": "Carbon Rod",     "price": 4000,   "max_rarity": "epic",
        "rarity_bonus": 12},
    4: {"name": "Ranger Rod",     "price": 20000,  "max_rarity": "legendary",
        "rarity_bonus": 20},
    5: {"name": "Void Rod",       "price": 100000, "max_rarity": "mythic",
        "rarity_bonus": 30},
    6: {"name": "Celestial Rod",  "price": 500000, "max_rarity": "ancient",
        "rarity_bonus": 45},
}

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "ancient"]

# Fish species. `id` must be stable forever once players can own one (it's the
# collection key) -- never renumber, only append.
# value = base sell price. min_rod_tier = lowest rod that can catch it.
FISH = [
    # id, name, emoji, rarity, value, min_rod_tier
    (1,  "Mudskipper",       "🐟", "common", 8,   1),
    (2,  "Bluegill",         "🐟", "common", 10,  1),
    (3,  "Perch",            "🐟", "common", 12,  1),
    (4,  "Catfish",          "🐟", "common", 14,  1),
    (5,  "Carp",             "🐠", "common", 15,  1),
    (6,  "Trout",            "🐠", "uncommon", 35,  1),
    (7,  "Bass",             "🐠", "uncommon", 42,  1),
    (8,  "Salmon",           "🐠", "uncommon", 50,  1),
    (9,  "Pike",             "🐡", "uncommon", 60,  1),
    (10, "Snapper",          "🐡", "rare", 150,  2),
    (11, "Swordfish",        "🗡️", "rare", 190,  2),
    (12, "Tuna",             "🐟", "rare", 220,  2),
    (13, "Electric Eel",     "⚡", "epic", 500,  3),
    (14, "Anglerfish",       "🏮", "epic", 650,  3),
    (15, "Golden Koi",       "🌟", "epic", 800,  3),
    (16, "Great White",      "🦈", "legendary", 2500, 4),
    (17, "Kraken Spawn",     "🐙", "legendary", 3200, 4),
    (18, "Phoenix Fish",     "🔥", "mythic", 15000, 5),
    (19, "Leviathan",        "🌊", "mythic", 20000, 5),
    (20, "Void Serpent",     "🌌", "mythic", 25000, 5),

    # -- added in v1.1: more variety per tier + the new "ancient" tier --
    (21, "Minnow",           "🐟", "common", 6,   1),
    (22, "Goldfish",         "🐟", "common", 9,   1),
    (23, "Sunfish",          "🐟", "common", 11,  1),
    (24, "Herring",          "🐠", "common", 13,  1),
    (25, "Sardine",          "🐠", "common", 9,   1),
    (26, "Mackerel",         "🐠", "uncommon", 38,  1),
    (27, "Walleye",          "🐡", "uncommon", 45,  1),
    (28, "Rainbow Trout",    "🌈", "uncommon", 55,  1),
    (29, "Barracuda",        "🐟", "rare", 175,  2),
    (30, "Stingray",         "🩵", "rare", 200,  2),
    (31, "Hammerhead",       "🦈", "rare", 260,  2),
    (32, "Manta Ray",        "🖤", "epic", 700,  3),
    (33, "Giant Squid",      "🦑", "epic", 900,  3),
    (34, "Crystal Trout",    "💎", "epic", 1100, 3),
    (35, "Storm Eel",        "⛈️", "legendary", 2800, 4),
    (36, "Sunken King",      "👑", "legendary", 3600, 4),
    (37, "Moonlit Ray",      "🌙", "legendary", 3000, 4),
    (38, "Starforged Koi",   "✨", "ancient", 60000, 6),
    (39, "World Serpent",    "🐍", "ancient", 80000, 6),
    (40, "Origin Fish",      "🌀", "ancient", 100000, 6),
]

FISH_BY_ID = {f[0]: f for f in FISH}

# Fishing cooldown in seconds
FISH_COOLDOWN = 30
DAILY_COOLDOWN_HOURS = 24
DAILY_STREAK_GRACE_HOURS = 48  # miss the window past this and streak resets
DAILY_BASE_REWARD = 200
DAILY_STREAK_BONUS_PER_DAY = 20
DAILY_STREAK_BONUS_CAP = 400
