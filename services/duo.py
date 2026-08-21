"""
Duo score — deterministic, explainable, and built only from things
Replay can actually observe in-guild. No fabricated "messages to each
other"; DMs are never read.

FORMULA
-------
Duo = round(100 * weighted_average(components))

  vc_together       (weight 0.40) -> min(hours_together / 10, 1.0)
  hour_overlap       (weight 0.25) -> shared active hours / 24
  channel_overlap    (weight 0.20) -> |channels_a ∩ channels_b| / |channels_a ∪ channels_b|
  active_day_overlap (weight 0.15) -> |days_a ∩ days_b| / |days_a ∪ days_b|

vc_together dominates because shared voice time is the strongest
real signal of an actual friendship, not just being in the same
server. The other three components measure "do your rhythms line up"
rather than raw activity, so two people with wildly different
message counts can still score well if they're active the same times.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DuoInputs:
    vc_seconds_together: int
    hours_a: set[int]
    hours_b: set[int]
    channels_a: set[int]
    channels_b: set[int]
    active_days_a: set[str]
    active_days_b: set[str]


WEIGHTS = {
    "vc_together": 0.40,
    "hour_overlap": 0.25,
    "channel_overlap": 0.20,
    "active_day_overlap": 0.15,
}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def compute_duo_score(inputs: DuoInputs) -> tuple[int, dict[str, float]]:
    vc_hours = inputs.vc_seconds_together / 3600
    components = {
        "vc_together": min(vc_hours / 10, 1.0),
        "hour_overlap": len(inputs.hours_a & inputs.hours_b) / 24,
        "channel_overlap": _jaccard(inputs.channels_a, inputs.channels_b),
        "active_day_overlap": _jaccard(inputs.active_days_a, inputs.active_days_b),
    }
    weighted = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    score = round(weighted * 100)
    return score, components


def best_shared_hour(hours_a: set[int], hours_b: set[int]) -> int | None:
    shared = hours_a & hours_b
    return min(shared) if shared else None
