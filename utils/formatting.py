from __future__ import annotations


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    if hours == 0:
        return f"{minutes}m"
    return f"{hours}h {minutes:02d}m"


def format_number(n: int) -> str:
    return f"{n:,}"


def format_hour(hour: int) -> str:
    if hour == 0:
        return "12am"
    if hour == 12:
        return "12pm"
    suffix = "am" if hour < 12 else "pm"
    display = hour if hour < 12 else hour - 12
    return f"{display}{suffix}"


def format_hour_range(hour: int) -> str:
    end = (hour + 1) % 24
    return f"{format_hour(hour)}–{format_hour(end)}"


def format_emoji_key(emoji_key: str) -> str:
    """emoji_key is either a raw unicode emoji or 'name:id' for custom emoji."""
    if ":" in emoji_key:
        name, emoji_id = emoji_key.rsplit(":", 1)
        return f"<:{name}:{emoji_id}>"
    return emoji_key
