from __future__ import annotations

import io
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 900, 1200

BG = (18, 18, 20)
FG = (240, 240, 240)
MUTED = (150, 150, 155)
ACCENT = (30, 215, 96)

FONT_DIR = Path(__file__).parent / "fonts"

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    key = (weight, size)
    if key not in _font_cache:
        path = FONT_DIR / f"Inter-{weight}.ttf"
        if path.exists():
            _font_cache[key] = ImageFont.truetype(str(path), size)
        else:
            # Falls back to Pillow's bundled default if no font asset is
            # shipped — keeps this from hard-crashing on a fresh checkout.
            _font_cache[key] = ImageFont.load_default(size=size)
    return _font_cache[key]


def font_bold(size: int) -> ImageFont.FreeTypeFont:
    return _font("Bold", size)


def font_regular(size: int) -> ImageFont.FreeTypeFont:
    return _font("Regular", size)


async def fetch_avatar(url: str, size: int = 160) -> Image.Image:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return circle_mask(img)


def circle_mask(img: Image.Image) -> Image.Image:
    size = img.size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def fallback_avatar(size: int = 160) -> Image.Image:
    img = Image.new("RGBA", (size, size), ACCENT + (255,))
    return circle_mask(img)


def new_card() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    return img, ImageDraw.Draw(img)


def to_bytes(img: Image.Image) -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
