RARITIES = {
    "common":    {"weight": 600, "color": 0x9E9E9E, "emoji": "⚪"},
    "uncommon":  {"weight": 250, "color": 0x4CAF50, "emoji": "🟢"},
    "rare":      {"weight": 100, "color": 0x2196F3, "emoji": "🔵"},
    "epic":      {"weight": 40,  "color": 0x9C27B0, "emoji": "🟣"},
    "legendary": {"weight": 9,   "color": 0xFF9800, "emoji": "🟠"},
    "mythic":    {"weight": 1,   "color": 0xF44336, "emoji": "🔴"},
}

RODS = {
    1: {"name": "Twig Rod",      "price": 0,     "max_rarity": "uncommon",
        "rarity_bonus": 0},
    2: {"name": "Oak Rod",       "price": 750,   "max_rarity": "rare",
        "rarity_bonus": 5},
    3: {"name": "Carbon Rod",    "price": 4000,  "max_rarity": "epic",
        "rarity_bonus": 12},
    4: {"name": "Ranger Rod",    "price": 20000, "max_rarity": "legendary",
        "rarity_bonus": 20},
    5: {"name": "Void Rod",      "price": 100000, "max_rarity": "mythic",
        "rarity_bonus": 30},
}

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]

FISH = [

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
]

FISH_BY_ID = {f[0]: f for f in FISH}

FISH_COOLDOWN = 30
DAILY_COOLDOWN_HOURS = 24
DAILY_STREAK_GRACE_HOURS = 48  
DAILY_BASE_REWARD = 200
DAILY_STREAK_BONUS_PER_DAY = 20
DAILY_STREAK_BONUS_CAP = 400
