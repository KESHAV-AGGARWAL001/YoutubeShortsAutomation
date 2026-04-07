"""
long_06_thumbnail.py — Long-Form YouTube Thumbnail Generator

Same dark cinematic style as 06_thumbnail.py but for long-form videos:
  - No #Shorts stripping needed (titles don't have it)
  - Title can use wider lines (long-form titles are longer)
  - 1280x720px standard YouTube thumbnail
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont

THUMB_W, THUMB_H = 1280, 720

FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

GRADIENT_TOP    = (8, 8, 20)
GRADIENT_BOTTOM = (20, 10, 35)

WHITE      = (255, 255, 255)
YELLOW     = (255, 215, 0)
RED_ACCENT = (220, 30, 30)
BLACK      = (0, 0, 0)


def load_font(size):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_dark_gradient():
    img  = Image.new("RGB", (THUMB_W, THUMB_H))
    draw = ImageDraw.Draw(img)
    for y in range(THUMB_H):
        ratio = y / THUMB_H
        r = int(GRADIENT_TOP[0] + (GRADIENT_BOTTOM[0] - GRADIENT_TOP[0]) * ratio)
        g = int(GRADIENT_TOP[1] + (GRADIENT_BOTTOM[1] - GRADIENT_TOP[1]) * ratio)
        b = int(GRADIENT_TOP[2] + (GRADIENT_BOTTOM[2] - GRADIENT_TOP[2]) * ratio)
        draw.line([(0, y), (THUMB_W, y)], fill=(r, g, b))
    return img


def add_subtle_grid(draw):
    for x in range(0, THUMB_W, 120):
        draw.line([(x, 0), (x, THUMB_H)], fill=(20, 20, 40))
    for y in range(0, THUMB_H, 120):
        draw.line([(0, y), (THUMB_W, y)], fill=(20, 20, 40))


def split_title_for_thumbnail(title):
    """
    Split long-form title into 2 display lines.
    No #Shorts to strip — just clean and split.
    """
    clean = title.strip().rstrip(".,!?-").strip()
    words = clean.upper().split()

    if len(words) <= 4:
        return " ".join(words), ""

    mid = len(words) // 2
    if len(words) > 6:
        mid = max(3, len(words) // 2 - 1)

    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])

    if len(line1) > 28:
        words_l1 = line1.split()[:5]
        line1 = " ".join(words_l1)
    if len(line2) > 28:
        words_l2 = line2.split()[:5]
        line2 = " ".join(words_l2)

    return line1, line2


def draw_text_with_border(draw, pos, text, font, fill, border_color=BLACK, border_width=4, anchor="mm"):
    x, y = pos
    for dx in range(-border_width, border_width + 1):
        for dy in range(-border_width, border_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=border_color, anchor=anchor)
    draw.text(pos, text, font=font, fill=fill, anchor=anchor)


def draw_title_two_color(img, draw, line, y_center, font_main, font_accent):
    words = line.split()
    if not words:
        return

    if len(words) == 1:
        draw_text_with_border(draw, (THUMB_W // 2, y_center), words[0],
                              font_accent, YELLOW, border_width=5)
        return

    main_text   = " ".join(words[:-1])
    accent_word = words[-1]

    bbox_main   = draw.textbbox((0, 0), main_text + " ", font=font_main, anchor="lt")
    bbox_accent = draw.textbbox((0, 0), accent_word, font=font_accent, anchor="lt")

    w_main   = bbox_main[2] - bbox_main[0]
    w_accent = bbox_accent[2] - bbox_accent[0]
    total_w  = w_main + w_accent

    start_x = (THUMB_W - total_w) // 2

    draw_text_with_border(
        draw, (start_x, y_center),
        main_text + " ", font_main, WHITE,
        border_width=4, anchor="lt"
    )

    draw_text_with_border(
        draw, (start_x + w_main, y_center),
        accent_word, font_accent, YELLOW,
        border_width=5, anchor="lt"
    )


def add_red_accent_bar(draw, y_bar):
    bar_h = 7
    bar_w = int(THUMB_W * 0.55)
    bar_x = (THUMB_W - bar_w) // 2
    draw.rectangle(
        [(bar_x, y_bar), (bar_x + bar_w, y_bar + bar_h)],
        fill=RED_ACCENT
    )
    draw.rectangle(
        [(bar_x - 10, y_bar - 2), (bar_x + bar_w + 10, y_bar + bar_h + 2)],
        fill=(220, 30, 30, 60)
    )


def add_channel_watermark(draw, font_small):
    watermark = "@NEXTLEVELMIND"
    draw_text_with_border(
        draw,
        (THUMB_W - 30, THUMB_H - 30),
        watermark, font_small, (200, 200, 200),
        border_width=2, anchor="rb"
    )


def generate_thumbnail(title):
    img  = create_dark_gradient()
    draw = ImageDraw.Draw(img)

    add_subtle_grid(draw)

    font_large  = load_font(110)
    font_accent = load_font(116)
    font_small  = load_font(32)

    line1, line2 = split_title_for_thumbnail(title)

    if line2:
        y1 = THUMB_H // 2 - 70
        y2 = THUMB_H // 2 + 70
        draw_title_two_color(img, draw, line1, y1, font_large, font_accent)
        add_red_accent_bar(draw, THUMB_H // 2 - 10)
        draw_title_two_color(img, draw, line2, y2, font_large, font_accent)
    else:
        draw_title_two_color(img, draw, line1, THUMB_H // 2, font_large, font_accent)
        add_red_accent_bar(draw, THUMB_H // 2 + 80)

    add_channel_watermark(draw, font_small)

    return img


def main():
    print("=" * 50)
    print("  Long-Form Thumbnail Generator")
    print("  Style: Dark cinematic + Yellow accent + Red bar")
    print("=" * 50)

    if not os.path.exists("output/seo_data.json"):
        print("\n  ERROR: output/seo_data.json not found!")
        return

    with open("output/seo_data.json", encoding="utf-8") as f:
        seo = json.load(f)

    title = seo["youtube_title"]
    print(f"\n  Title   : {title}")

    print("\n  Generating thumbnail...")
    img = generate_thumbnail(title)
    img = img.resize((1280, 720), Image.LANCZOS)
    img.save("output/thumbnail.jpg", quality=97, optimize=True)

    print("\n" + "=" * 50)
    print("  Done! Thumbnail saved: output/thumbnail.jpg")
    print("  Size: 1280x720 | Style: Dark cinematic (long-form)")
    print("=" * 50)
    print("\n  Next step: Run long_07_upload.py")


if __name__ == "__main__":
    main()
