"""Small text helpers shared by every log layout."""


def trim(text: str | None, limit: int = 500) -> str:
    if not text:
        return "*None*"
    text = text.replace("```", "'''")
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def user_line(user) -> str:
    if user is None:
        return "Unknown"
    return f"{user.mention} (`{user.id}`)"


def channel_line(channel) -> str:
    if channel is None:
        return "Unknown"
    return f"{channel.mention} (`{channel.id}`)"
