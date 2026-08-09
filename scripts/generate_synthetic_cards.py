#!/usr/bin/env python3
"""Generate printable synthetic business-card PNGs for local OCR tests."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic"
SEED = ROOT / "backend" / "app" / "seed" / "data.py"


def _load_cards():
    # Import without installing package
    import importlib.util
    import sys

    sys.path.insert(0, str(ROOT / "backend"))
    from app.seed.data import SEED_CARDS

    return SEED_CARDS


STYLES = [
    {"bg": (18, 42, 48), "fg": (236, 244, 242), "accent": (90, 196, 186)},
    {"bg": (248, 246, 240), "fg": (28, 28, 28), "accent": (20, 90, 84)},
    {"bg": (30, 30, 34), "fg": (240, 240, 240), "accent": (220, 180, 100)},
    {"bg": (235, 242, 248), "fg": (16, 40, 64), "accent": (40, 110, 160)},
]


def render_card(card: dict, style: dict, path: Path) -> None:
    w, h = 1050, 600
    img = Image.new("RGB", (w, h), style["bg"])
    draw = ImageDraw.Draw(img)
    try:
        font_lg = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 48)
        font_md = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    except OSError:
        font_lg = font_md = font_sm = ImageFont.load_default()

    draw.rectangle([0, 0, 18, h], fill=style["accent"])
    y = 70
    draw.text((60, y), card["full_name"], fill=style["fg"], font=font_lg)
    y += 70
    draw.text((60, y), card.get("title") or "", fill=style["accent"], font=font_md)
    y += 44
    draw.text((60, y), card.get("company") or "", fill=style["fg"], font=font_md)
    y += 70
    for line in (
        card.get("email") or "",
        card.get("phone") or "",
        f"{card.get('region') or ''} · {card.get('timezone') or ''}",
        " · ".join(card.get("tags") or []),
    ):
        draw.text((60, y), line, fill=style["fg"], font=font_sm)
        y += 36

    img.save(path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cards = _load_cards()
    manifest = []
    for i, card in enumerate(cards):
        style = STYLES[i % len(STYLES)]
        name = f"card_{i+1:02d}_{card['full_name'].lower().replace(' ', '_')}.png"
        path = OUT / name
        render_card(card, style, path)
        manifest.append({"file": name, **card})
        print("wrote", path)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(cards)} synthetic cards in {OUT}")


if __name__ == "__main__":
    main()
