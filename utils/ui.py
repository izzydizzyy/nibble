"""
Components V2 UI builders shared across cogs, so every command looks like
it came from the same bot instead of every cog rolling its own embed.
https://discord.com/developers/docs/components/reference (Components V2)

All of these return a discord.ui.LayoutView, sent via
interaction.response.send_message(view=view) -- no `embed=` needed, and
Discord infers the "components v2" message flag automatically from the
view type.
"""
import discord
from discord import ui

import config
import emojis as em
import game_data as gd

BRAND = "-# 🐱 NIBBLE"


def _bar(pct: float, width: int = 10) -> str:
    filled = round(pct * width)
    return "█" * filled + "░" * (width - filled)


class SimpleView(ui.LayoutView):
    """A single accented container of text -- the workhorse for most
    command responses (catches, sells, purchases, errors)."""

    def __init__(self, lines: list[str], *, accent: int = 0x2B2D31, timeout=None):
        super().__init__(timeout=timeout)
        container = ui.Container(
            ui.TextDisplay("\n".join(lines)),
            accent_colour=accent,
        )
        self.add_item(container)


def _format_duration(seconds: float) -> str:
    seconds = max(seconds, 0)
    if seconds >= 3600:
        h, m = int(seconds // 3600), int((seconds % 3600) // 60)
        return f"{h}h {m}m"
    if seconds >= 60:
        m, s = int(seconds // 60), int(seconds % 60)
        return f"{m}m {s}s"
    return f"{seconds:.0f}s"


# Rarities get progressively more presentation as they get rarer:
#  plain    -- headline + one meta line. That's it.
#  notable  -- meta line gains a size, and a new discovery shows collection
#              progress.
#  standout -- a card (Section + Thumbnail) with Nibble's reaction art and a
#              short line of flavor text, reserved for catches worth
#              stopping to look at.
_PLAIN_RARITIES = {"common", "uncommon"}
_STANDOUT_RARITIES = {"legendary", "mythic", "ancient"}

_STANDOUT_FLAVOR = {
    "legendary": "A legendary find.",
    "mythic": "One of the rarest catches in Nibble.",
    "ancient": "Astronomically rare — most anglers never see one of these.",
}


def catch_view(*, name, emoji, rarity, value, is_new, owned_qty,
               weight=None, unique_species=None, total_species=None) -> ui.LayoutView:
    info = gd.RARITIES[rarity]
    headline = f"{emoji} You caught a **{name}**!"
    meta = f"`{rarity.title()}` · {value:,} {config.CURRENCY_EMOJI}"
    if rarity not in _PLAIN_RARITIES and weight is not None:
        meta += f" · {weight} lb"

    body = [headline, meta]

    if is_new:
        body.append("")
        body.append("**New discovery!**")
        if rarity not in _PLAIN_RARITIES and unique_species and total_species:
            body.append(f"-# {unique_species}/{total_species} species discovered")
        else:
            body.append("-# Added to your collection.")

    view = ui.LayoutView(timeout=None)

    if rarity in _STANDOUT_RARITIES:
        body.append("")
        body.append(f"-# {_STANDOUT_FLAVOR[rarity]}")

        reaction_id = em.RARITY_REACTION_IDS.get(rarity)
        section = ui.Section(
            ui.TextDisplay("\n".join(body)),
            accessory=ui.Thumbnail(media=em.emoji_cdn_url(reaction_id)),
        )
        container = ui.Container(section, accent_colour=info["color"])
    else:
        container = ui.Container(ui.TextDisplay("\n".join(body)), accent_colour=info["color"])

    view.add_item(container)
    return view


def cooldown_view(seconds_left: float, *, kind: str = "fish") -> ui.LayoutView:
    verb = "Cast again" if kind == "fish" else "Claim again"
    lines = [f"🎣 {verb} in **{_format_duration(seconds_left)}**."]
    return SimpleView(lines, accent=0x4E5058)


def daily_view(*, reward: int, streak: int) -> ui.LayoutView:
    lines = [
        BRAND,
        f"### 🎁 Daily Reward Claimed",
        f"{em.NIBBLE_HYPE} You received **{reward:,}** {config.CURRENCY_EMOJI} {config.CURRENCY_NAME}",
        f"🔥 Streak: **{streak}** day{'s' if streak != 1 else ''}",
    ]
    return SimpleView(lines, accent=0xFFC107)


def profile_view(*, target, user_row, unique_fish, total_species) -> ui.LayoutView:
    rod = gd.RODS[user_row["rod_tier"]]
    pct = unique_fish / total_species if total_species else 0
    lines = [
        BRAND,
        f"### 🐱 {target.display_name}'s Profile",
        f"**Balance** — {config.CURRENCY_EMOJI} {user_row['balance']:,} {config.CURRENCY_NAME}",
        f"**Rod** — {rod['name']} (Tier {user_row['rod_tier']})",
        f"**Daily Streak** — 🔥 {user_row['daily_streak']}",
        f"**Fish Caught** — 🎣 {user_row['total_fish']:,}",
        "",
        f"**Collection** — {unique_fish}/{total_species} species",
        f"`{_bar(pct)}` {pct*100:.0f}%",
    ]
    return SimpleView(lines, accent=0x03A9F4)


def inventory_view(*, target, rows) -> ui.LayoutView:
    if not rows:
        lines = [
            BRAND,
            f"### 🎒 {target.display_name}'s Inventory",
            f"{em.NIBBLE_CRY} Empty. Go `/fish` to catch something.",
        ]
        return SimpleView(lines, accent=0x4E5058)

    by_rarity: dict[str, list[str]] = {}
    total_value = 0
    for row in rows:
        f = gd.FISH_BY_ID[row["fish_id"]]
        _, name, emoji, rarity, value, _ = f
        qty = row["quantity"]
        total_value += value * qty
        by_rarity.setdefault(rarity, []).append(f"{emoji} **{name}** ×{qty} — {value:,} ea")

    lines = [BRAND, f"### 🎒 {target.display_name}'s Inventory"]
    for rarity in reversed(gd.RARITY_ORDER):
        entries = by_rarity.get(rarity)
        if not entries:
            continue
        info = gd.RARITIES[rarity]
        lines.append(f"\n{info['emoji']} **{rarity.title()}**")
        lines.extend(f"　{e}" for e in entries[:15])

    container = ui.Container(
        ui.TextDisplay("\n".join(lines)),
        ui.Separator(),
        ui.TextDisplay(f"💰 Total sell value: **{total_value:,}** {config.CURRENCY_NAME}"),
        accent_colour=0x795548,
    )
    view = ui.LayoutView(timeout=None)
    view.add_item(container)
    return view


def collection_view(*, target, owned_ids, total_species) -> ui.LayoutView:
    lines = [
        BRAND,
        f"### 📖 {target.display_name}'s Collection",
        f"{len(owned_ids)}/{total_species} species discovered",
    ]
    for rarity in gd.RARITY_ORDER:
        info = gd.RARITIES[rarity]
        entries = []
        for fish_id, name, emoji, r, value, _ in gd.FISH:
            if r != rarity:
                continue
            entries.append(f"{emoji} {name}" if fish_id in owned_ids else "❓ ???")
        lines.append(f"\n{info['emoji']} **{rarity.title()}**")
        lines.append(" · ".join(entries))

    container = ui.Container(ui.TextDisplay("\n".join(lines)), accent_colour=0x00BCD4)
    view = ui.LayoutView(timeout=None)
    view.add_item(container)
    return view


def sell_view(*, name, emoji, quantity, payout) -> ui.LayoutView:
    lines = [
        BRAND,
        f"### 💰 Sold",
        f"{emoji} **{quantity}x {name}** → **{payout:,}** {config.CURRENCY_EMOJI} {config.CURRENCY_NAME}",
    ]
    return SimpleView(lines, accent=0x2ECC71)


def sell_all_view(*, count, total, rarity_filter=None) -> ui.LayoutView:
    filt = f" ({rarity_filter.title()} only)" if rarity_filter else ""
    lines = [
        BRAND,
        f"### 💰 Sold {count} fish{filt}",
        f"Total payout: **{total:,}** {config.CURRENCY_EMOJI} {config.CURRENCY_NAME}",
    ]
    return SimpleView(lines, accent=0x2ECC71)


def shop_view(*, user_row) -> ui.LayoutView:
    lines = [BRAND, f"### 🛒 Rod Shop"]
    for tier, rod in gd.RODS.items():
        if tier < user_row["rod_tier"]:
            status = "✅ owned"
        elif tier == user_row["rod_tier"]:
            status = "⬅️ **equipped**"
        else:
            status = f"**{rod['price']:,}** {config.CURRENCY_EMOJI}"
        lines.append(
            f"\n**Tier {tier} — {rod['name']}**\n"
            f"　up to {gd.RARITIES[rod['max_rarity']]['emoji']} {rod['max_rarity'].title()} fish · {status}"
        )
    lines.append("\n-# Buy with `/buy tier:<n>` — rods must be bought in order.")

    container = ui.Container(ui.TextDisplay("\n".join(lines)), accent_colour=0x8BC34A)
    view = ui.LayoutView(timeout=None)
    view.add_item(container)
    return view


def buy_view(*, rod_name, max_rarity) -> ui.LayoutView:
    lines = [
        BRAND,
        f"### 🎣 New Rod Equipped",
        f"{em.NIBBLE_HYPE} You bought the **{rod_name}**!",
        f"You can now catch up to {gd.RARITIES[max_rarity]['emoji']} **{max_rarity.title()}** fish.",
    ]
    return SimpleView(lines, accent=0x8BC34A)


def leaderboard_view(*, category: str, rows, fish_total: int) -> ui.LayoutView:
    if category == "wealth":
        title = "🏆 Richest Nibblers"
        entries = [
            f"**#{i+1}** <@{r['user_id']}> — {r['balance']:,} {config.CURRENCY_EMOJI}"
            for i, r in enumerate(rows)
        ]
    else:
        title = "🏆 Top Collectors"
        entries = [
            f"**#{i+1}** <@{r['user_id']}> — {r['unique_fish']}/{fish_total} species"
            for i, r in enumerate(rows)
        ]
    if not entries:
        entries = [f"{em.NIBBLE_CRY} No data yet — be the first!"]

    lines = [BRAND, f"### {title}"] + entries
    return SimpleView(lines, accent=0xFFD700)


def error_view(message: str) -> ui.LayoutView:
    lines = [BRAND, f"### ⚠️ {message}"]
    return SimpleView(lines, accent=0xED4245)
