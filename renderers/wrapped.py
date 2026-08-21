from __future__ import annotations

import io

from renderers.base import (
    ACCENT, BG, FG, MUTED, fallback_avatar, fetch_avatar, font_bold, font_regular, new_card, to_bytes,
)

MARGIN = 60


async def render_wrapped(
    *,
    username: str,
    period_label: str,
    avatar_url: str | None,
    stats: list[tuple[str, str]],
    personality: str,
) -> io.BytesIO:
    img, draw = new_card()

    draw.text((MARGIN, 50), "REPLAY", font=font_bold(28), fill=ACCENT)

    try:
        avatar = await fetch_avatar(avatar_url) if avatar_url else fallback_avatar()
    except Exception:
        avatar = fallback_avatar()
    img.paste(avatar, (MARGIN, 110), avatar)

    text_x = MARGIN + avatar.width + 30
    draw.text((text_x, 130), username, font=font_bold(40), fill=FG)
    draw.text((text_x, 185), period_label, font=font_regular(22), fill=MUTED)

    y = 330
    for label, value in stats:
        draw.text((MARGIN, y), value, font=font_bold(48), fill=FG)
        draw.text((MARGIN, y + 58), label, font=font_regular(22), fill=MUTED)
        y += 120

    y += 20
    draw.line((MARGIN, y, img.width - MARGIN, y), fill=(40, 40, 44), width=2)
    y += 40
    draw.text((MARGIN, y), "your replay type", font=font_regular(20), fill=MUTED)
    draw.text((MARGIN, y + 30), personality.upper(), font=font_bold(38), fill=ACCENT)

    return to_bytes(img)
