import random

import game_data as gd


def roll_fish(rod_tier: int) -> tuple:
    """Pick a random fish species the given rod tier is allowed to catch,
    weighted by rarity (with the rod's bonus nudging odds toward rarer
    tiers). Returns a row from game_data.FISH."""
    rod = gd.RODS[rod_tier]
    max_rarity_idx = gd.RARITY_ORDER.index(rod["max_rarity"])
    allowed_rarities = gd.RARITY_ORDER[: max_rarity_idx + 1]

    # Build weighted pool of allowed rarities, applying the rod's bonus to
    # shift weight away from "common" and toward the rarer tiers it unlocks.
    weights = {}
    for r in allowed_rarities:
        base = gd.RARITIES[r]["weight"]
        if r == "common":
            weights[r] = max(base - rod["rarity_bonus"] * 4, 10)
        else:
            weights[r] = base + rod["rarity_bonus"]

    rarity = random.choices(list(weights.keys()), weights=list(weights.values()))[0]

    candidates = [
        f for f in gd.FISH if f[3] == rarity and f[5] <= rod_tier
    ]
    if not candidates:
        # Fallback: any fish this rod can legally catch.
        candidates = [f for f in gd.FISH if f[5] <= rod_tier]

    return random.choice(candidates)


def roll_weight(rarity: str) -> float:
    """Cosmetic size for a catch, in lbs. Not stored -- just flavor text
    shown on the catch card."""
    lo, hi = gd.WEIGHT_RANGES[rarity]
    return round(random.uniform(lo, hi), 1)

