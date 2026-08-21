"""Central config. Everything secret/env-specific lives here so nothing else
in the codebase touches os.environ directly."""
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID") or None
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/nibble.db")

CURRENCY_NAME = "Nibbles"
CURRENCY_EMOJI = "🐟"

if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in."
    )
