from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_zone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def local_date_and_hour(moment_utc: datetime, tz_name: str) -> tuple[str, int]:
    local = moment_utc.astimezone(get_zone(tz_name))
    return local.date().isoformat(), local.hour


def period_start(period: str, tz_name: str) -> str | None:
    """Returns the ISO date a `/wrapped period:` window starts on, or
    None for all-time."""
    today = datetime.now(get_zone(tz_name)).date()
    if period == "week":
        return (today - timedelta(days=7)).isoformat()
    if period == "month":
        return (today - timedelta(days=30)).isoformat()
    if period == "all-time":
        return None
    if period.isdigit() and len(period) == 4:
        return date(int(period), 1, 1).isoformat()
    return None
