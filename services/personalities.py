"""
Deterministic archetype assignment. Checked in priority order — the
first matching rule wins, so order encodes precedence (e.g. someone
who is both night-heavy and VC-heavy gets Night Owl first since a
timing pattern is a stronger "identity" signal than raw hours).

Every threshold below is intentionally documented so it can be tuned
without guessing at what "should" trigger a type.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PersonalityInputs:
    total_messages: int
    active_days: int
    voice_hours_total: float
    night_pct: float          # fraction of messages sent between 12am-5am
    reactions_given: int
    distinct_channels: int
    top_game_hours: float
    top_artist_observations: int
    days_since_first_seen: int


def assign_personality(i: PersonalityInputs) -> tuple[str, str]:
    """Returns (name, one-line description)."""

    if i.days_since_first_seen >= 3 and i.total_messages == 0 and i.voice_hours_total == 0:
        return "The Ghost", "in the server, technically"

    if i.night_pct >= 0.35 and i.total_messages >= 20:
        return "The Night Owl", "most active between midnight and 5am"

    if i.voice_hours_total >= 20 and i.voice_hours_total >= i.total_messages / 20:
        return "The VC Dweller", "lives in voice chat"

    if i.total_messages >= 15 and i.reactions_given / max(i.total_messages, 1) >= 1.5:
        return "The Reactor", "reacts more than they type"

    if i.top_game_hours >= 15:
        return "The Gamer", "usually mid-game"

    if i.top_artist_observations >= 10:
        return "The Listener", "always has something playing"

    if i.total_messages >= 50 and i.distinct_channels <= 2:
        return "The Yapper", "one channel, endless messages"

    if i.distinct_channels >= 6:
        return "The Everywhere User", "shows up in every channel"

    if i.active_days >= 1 and i.total_messages <= 10 and i.voice_hours_total < 1:
        return "The Lurker", "watching, mostly"

    return "The Regular", "steady, reliable activity"
