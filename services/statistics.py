from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from database.repositories.guilds import GuildRepository
from database.repositories.messages import MessageRepository
from database.repositories.presence import PresenceRepository
from database.repositories.reactions import ReactionRepository
from database.repositories.voice import VoiceRepository
from services.aura import AuraInputs, compute_aura
from services.personalities import PersonalityInputs, assign_personality


@dataclass
class UserProfile:
    user_id: int
    guild_id: int
    total_messages: int
    active_days: int
    voice_hours_total: float
    top_channel_id: str | None
    favorite_hour: int | None
    top_emoji: str | None
    streak_current: int
    streak_longest: int
    aura_score: int
    aura_components: dict[str, float]
    personality: str
    personality_desc: str
    tracking_since: str | None


class StatisticsService:
    def __init__(self, messages: MessageRepository, voice: VoiceRepository,
                 reactions: ReactionRepository, presence: PresenceRepository,
                 guilds: GuildRepository):
        self.messages = messages
        self.voice = voice
        self.reactions = reactions
        self.presence = presence
        self.guilds = guilds

    async def build_profile(self, guild_id: int, user_id: int) -> UserProfile:
        totals = await self.messages.totals(guild_id, user_id)
        active_days = await self.messages.active_days(guild_id, user_id)
        voice_seconds = await self.voice.total_seconds(guild_id, user_id)
        top_channel = await self.messages.top_channel(guild_id, user_id)
        favorite_hour = await self.messages.favorite_hour(guild_id, user_id)
        top_emoji = await self.reactions.top_emoji(guild_id, user_id)
        streak = await self.messages.streak(guild_id, user_id)
        tracking_since = await self.guilds.tracking_since(guild_id, user_id)

        since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        msgs_30d = await self.messages.totals_since(guild_id, user_id, since_30d)
        voice_30d = await self.voice.seconds_since(guild_id, user_id, since_30d)
        reactions_30d = await self.reactions.total_given(guild_id, user_id)  # all-time proxy
        hourly = await self.messages.hourly_distribution(guild_id, user_id)
        channels_used = await self.messages.channels_used(guild_id, user_id)
        distinct_channels = len(channels_used)

        aura_score, aura_components = compute_aura(AuraInputs(
            active_days_30d=min(active_days, 30),
            current_streak=streak["current"],
            voice_hours_30d=voice_30d / 3600,
            reactions_given_30d=reactions_30d,
            distinct_channels=distinct_channels,
            distinct_active_hours=len(hourly),
        ))

        night_messages = sum(c for h, c in hourly.items() if h < 5)
        night_pct = night_messages / totals["total"] if totals["total"] else 0.0

        games = await self.presence.top_games(guild_id, user_id, limit=1)
        top_game_hours = games[0]["estimated_seconds"] / 3600 if games else 0.0
        top_artist = await self.presence.top_artist(guild_id, user_id)
        top_artist_obs = top_artist["total"] if top_artist else 0

        days_since_first_seen = 0
        if tracking_since:
            started = datetime.fromisoformat(tracking_since)
            days_since_first_seen = (datetime.now(timezone.utc) - started).days

        personality, personality_desc = assign_personality(PersonalityInputs(
            total_messages=totals["total"],
            active_days=active_days,
            voice_hours_total=voice_seconds / 3600,
            night_pct=night_pct,
            reactions_given=reactions_30d,
            distinct_channels=distinct_channels,
            top_game_hours=top_game_hours,
            top_artist_observations=top_artist_obs,
            days_since_first_seen=days_since_first_seen,
        ))

        return UserProfile(
            user_id=user_id,
            guild_id=guild_id,
            total_messages=totals["total"],
            active_days=active_days,
            voice_hours_total=voice_seconds / 3600,
            top_channel_id=top_channel[0] if top_channel else None,
            favorite_hour=favorite_hour,
            top_emoji=top_emoji[0] if top_emoji else None,
            streak_current=streak["current"],
            streak_longest=streak["longest"],
            aura_score=aura_score,
            aura_components=aura_components,
            personality=personality,
            personality_desc=personality_desc,
            tracking_since=tracking_since,
        )

    async def has_enough_data(self, guild_id: int, user_id: int, minimum_messages: int = 5) -> bool:
        totals = await self.messages.totals(guild_id, user_id)
        voice_seconds = await self.voice.total_seconds(guild_id, user_id)
        return totals["total"] >= minimum_messages or voice_seconds >= 300
