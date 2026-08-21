"""
Schema is plain SQL rather than an ORM so it stays easy to port to
Postgres later (types are intentionally boring: INTEGER, TEXT, REAL).

Design notes:
- Discord snowflakes are stored as TEXT. They fit in a 64-bit int, but
  keeping them as text avoids any risk of float coercion via drivers
  and makes the eventual Postgres migration (BIGINT vs NUMERIC) a
  non-issue either way.
- Activity is pre-aggregated into daily/hourly buckets instead of one
  row per event, so `/wrapped` and `/leaderboard` queries stay cheap
  even at scale. Raw voice_sessions are the one exception, kept because
  "longest session" and "people you're in VC with" need session-level
  detail.
"""

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS guilds (
    guild_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    exclude_solo_vc INTEGER NOT NULL DEFAULT 1,
    track_presence INTEGER NOT NULL DEFAULT 1,
    track_messages INTEGER NOT NULL DEFAULT 1,
    track_voice INTEGER NOT NULL DEFAULT 1,
    joined_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    avatar_key TEXT,
    first_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS guild_members (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    tracking_since TEXT NOT NULL,
    opted_out INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

-- One row per (guild, user, channel, date). Bumped on every message.
CREATE TABLE IF NOT EXISTS message_daily (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    date TEXT NOT NULL,             -- YYYY-MM-DD in the guild's timezone
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id, channel_id, date)
);

-- Hour-of-day histogram per user per guild, all-time. Small and cheap
-- to keep forever; used for "favorite hour" / night-owl detection.
CREATE TABLE IF NOT EXISTS message_hourly (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    hour INTEGER NOT NULL,          -- 0-23, local to guild timezone
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id, hour)
);

CREATE TABLE IF NOT EXISTS user_streaks (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_active_date TEXT,
    PRIMARY KEY (guild_id, user_id)
);

-- Closed voice sessions only; the "currently open" session for a
-- member lives in memory in the voice tracker and is flushed here
-- on leave/switch/disconnect/bot-shutdown.
CREATE TABLE IF NOT EXISTS voice_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    was_solo INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_lookup
    ON voice_sessions (guild_id, user_id, started_at);

-- Per-day rollup so /vcstats and /wrapped don't scan raw sessions.
CREATE TABLE IF NOT EXISTS voice_daily (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    seconds INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id, date)
);

-- Overlapping VC time between two users, keyed with user_a < user_b
-- (string comparison) so each pair has exactly one row.
CREATE TABLE IF NOT EXISTS voice_pairs (
    guild_id TEXT NOT NULL,
    user_a TEXT NOT NULL,
    user_b TEXT NOT NULL,
    seconds_together INTEGER NOT NULL DEFAULT 0,
    last_together TEXT,
    PRIMARY KEY (guild_id, user_a, user_b)
);

CREATE INDEX IF NOT EXISTS idx_voice_pairs_user_a ON voice_pairs (guild_id, user_a);
CREATE INDEX IF NOT EXISTS idx_voice_pairs_user_b ON voice_pairs (guild_id, user_b);

CREATE TABLE IF NOT EXISTS reaction_stats (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    emoji_key TEXT NOT NULL,        -- unicode emoji or "name:id" for custom
    given_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, user_id, emoji_key)
);

CREATE TABLE IF NOT EXISTS emoji_stats (
    guild_id TEXT NOT NULL,
    emoji_key TEXT NOT NULL,
    total_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, emoji_key)
);

-- Sparse presence samples. We don't get a continuous feed, so game
-- time is an estimate built from observed start/end pairs, not a
-- claim of exact playtime.
CREATE TABLE IF NOT EXISTS game_stats (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    game_name TEXT NOT NULL,
    estimated_seconds INTEGER NOT NULL DEFAULT 0,
    sessions_observed INTEGER NOT NULL DEFAULT 0,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id, game_name)
);

CREATE TABLE IF NOT EXISTS music_stats (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    artist TEXT NOT NULL,
    track TEXT NOT NULL,
    observed_count INTEGER NOT NULL DEFAULT 0,
    estimated_seconds INTEGER NOT NULL DEFAULT 0,
    last_seen TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id, artist, track)
);

-- In-progress presence activities, so we can compute a duration when
-- the activity ends. One open row per (guild, user, activity type).
CREATE TABLE IF NOT EXISTS presence_sessions (
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,             -- 'game' or 'music'
    name TEXT NOT NULL,             -- game name, or "artist||track"
    started_at TEXT NOT NULL,
    PRIMARY KEY (guild_id, user_id, kind)
);
"""
