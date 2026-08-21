"""
Aura score — a deterministic 0-9999 number built from *variety* of
participation, not raw volume. Someone who is active every day across
messages, VC, and reactions scores higher than someone who sends 10x
the messages but does nothing else. This is a design choice (see spec:
"avoid rewarding unhealthy levels of nonstop Discord use").

FORMULA
-------
Aura = round(9999 * weighted_average(components))

Components (each normalized to 0-1 via a soft cap, so there's no
benefit to grinding past a reasonable ceiling):

  message_activity  (weight 0.20) -> active_days / 30, capped at 1.0
  message_consistency (weight 0.15) -> current_streak / 14, capped at 1.0
  voice_activity     (weight 0.20) -> vc_hours_last_30d / 40, capped at 1.0
  reaction_engagement (weight 0.15) -> reactions_given_last_30d / 60, capped at 1.0
  channel_variety    (weight 0.15) -> distinct_channels_used / 6, capped at 1.0
  hour_variety       (weight 0.15) -> distinct_active_hours / 12, capped at 1.0

Each cap is a "healthy regular use" ceiling, not a max-possible-activity
ceiling — e.g. 40 VC hours/month is ~1.3hrs/day, not a grind target.
Going past the cap doesn't add score, which is the intentional
anti-"more hours = better" mechanism.

All inputs come from real tracked data. No randomness anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuraInputs:
    active_days_30d: int
    current_streak: int
    voice_hours_30d: float
    reactions_given_30d: int
    distinct_channels: int
    distinct_active_hours: int


WEIGHTS = {
    "message_activity": 0.20,
    "message_consistency": 0.15,
    "voice_activity": 0.20,
    "reaction_engagement": 0.15,
    "channel_variety": 0.15,
    "hour_variety": 0.15,
}


def _capped(value: float, cap: float) -> float:
    return min(value / cap, 1.0) if cap > 0 else 0.0


def compute_aura(inputs: AuraInputs) -> tuple[int, dict[str, float]]:
    components = {
        "message_activity": _capped(inputs.active_days_30d, 30),
        "message_consistency": _capped(inputs.current_streak, 14),
        "voice_activity": _capped(inputs.voice_hours_30d, 40),
        "reaction_engagement": _capped(inputs.reactions_given_30d, 60),
        "channel_variety": _capped(inputs.distinct_channels, 6),
        "hour_variety": _capped(inputs.distinct_active_hours, 12),
    }
    weighted = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(weighted * 9999)
    return score, components
