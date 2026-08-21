from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_list(name: str) -> list[int]:
    raw = os.getenv(name, "")
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


@dataclass(frozen=True)
class Config:
    token: str
    dev_guild_id: int | None
    database_path: Path
    owner_ids: list[int] = field(default_factory=list)
    exclude_solo_vc_default: bool = True
    log_level: str = "INFO"

    @classmethod
    def load(cls) -> "Config":
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

        dev_guild_raw = os.getenv("DEV_GUILD_ID")
        dev_guild_id = int(dev_guild_raw) if dev_guild_raw else None

        db_path = Path(os.getenv("DATABASE_PATH", "data/replay.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return cls(
            token=token,
            dev_guild_id=dev_guild_id,
            database_path=db_path,
            owner_ids=_get_int_list("OWNER_IDS"),
            exclude_solo_vc_default=_get_bool("EXCLUDE_SOLO_VC", True),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


config = Config.load()
