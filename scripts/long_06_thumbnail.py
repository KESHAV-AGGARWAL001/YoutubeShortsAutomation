"""
long_06_thumbnail.py — AI-Generated Long-Form YouTube Thumbnail (Gemini Image Generation)

Uses Gemini's native image generation (Nano Banana) to create unique,
eye-catching thumbnails for long-form videos based on the title and topic.

Falls back to programmatic dark gradient style if Gemini generation fails.
"""

import os
import json
import random
import base64
import time as _time
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# ── Gemini Setup ─────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai.types import GenerateContentConfig, Modality
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_IMAGE_AVAILABLE = True
except Exception:
    GEMINI_IMAGE_AVAILABLE = False

IMAGE_MODEL = "gemini-2.5-flash-preview-04-17"

THUMB_W, THUMB_H = 1280, 720

# ── Thumbnail prompt styles — randomly selected each run ─────────────
THUMBNAIL_PROMPTS = [
    # Style A — Dark cinematic
    """Create a YouTube thumbnail image (1280x720).
Style: Dark, cinematic, moody atmosphere with dramatic lighting.
Color scheme: Deep blacks, dark blues, subtle golden/amber highlights.
Include bold, large white text that says: "{title}"
The text should be centered, easy to read with a dark shadow/outline.
Make it look professional, high-contrast, and eye-catching.
NO faces, NO people. Focus on abstract dark visuals with dramatic light rays or particles.""",

    # Style B — Neon/futuristic
    """Create a YouTube thumbnail image (1280x720).
Style: Futuristic, neon-lit, cyberpunk-inspired dark background.
Color scheme: Dark background with neon blue, purple, or red glowing accents.
Include bold, large glowing white text that says: "{title}"
The text should be prominent, centered, with a neon glow effect.
Add subtle geometric shapes or light streaks in the background.
NO faces, NO people. Abstract futuristic visuals only.""",

    # Style C — Motivational dark
    """Create a YouTube thumbnail image (1280x720).
Style: Inspirational, powerful, dark background with a spotlight effect.
Color scheme: Black/dark gray background with a warm golden spotlight from above.
Include bold, large text that says: "{title}"
Top portion of text in white, one key word highlighted in bright gold/yellow.
Add subtle smoke or fog effects at the bottom.
NO faces, NO people. Clean, powerful composition.""",

    # Style D — Minimalist bold
    """Create a YouTube thumbnail image (1280x720).
Style: Clean, minimalist, high-impact.
Color scheme: Solid dark background (near black) with one accent color (red or orange).
Include very large, bold white text that says: "{title}"
Text should take up most of the image. One word in red/orange for emphasis.
Add a subtle red accent line or bar element.
NO faces, NO people. Typography-focused design.""",
]


def clean_title_for_thumbnail(title):
    """Clean title for thumbnail text — trim and truncate if needed."""
    clean = title.strip().rstrip(".,!?—-").strip()
    # Long-form titles can be longer, allow up to 80 chars
    if len(clean) > 80:
        words = clean.split()
        clean = " ".join(words[:10])
    return clean


def generate_thumbnail_gemini(title):
    """Generate thumbnail using Gemini's native image generation."""
    clean_title = clean_title_for_thumbnail(title)
    prompt_template = random.choice(THUMBNAIL_PROMPTS)
    prompt = prompt_template.format(title=clean_title)

    print(f"  Generating with Gemini image model...")

    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  Retry {attempt}/2 — waiting {wait}s...")
                _time.sleep(wait)

            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=prompt,
                config=GenerateContentConfig(
                    response_modalities=[Modality.TEXT, Modality.IMAGE],
                ),
            )

            # Extract image from response
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    img = Image.open(BytesIO(image_bytes))
                    img = img.convert("RGB")
                    img = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
                    print(f"  Gemini thumbnail generated successfully!")
                    return img

            print(f"  No image in Gemini response — retrying...")

        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate", "unavailable", "503", "500"]):
                if attempt < 2:
                    continue
            print(f"  Gemini image generation failed: {e}")
            return None

    return None


# ── Fallback: Programmatic thumbnail (PIL) ───────────────────────────

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

THUMB_TAGLINES = [
    "WATCH THIS BEFORE IT'S TOO LATE",
    "THIS CHANGES EVERYTHING",
    "YOU NEED TO HEAR THIS",
    "MOST PEOPLE WILL IGNORE THIS",
    "THE TRUTH NO ONE WILL TELL YOU",
    "THIS VIDEO WILL CHANGE YOUR LIFE",
    "STOP EVERYTHING AND WATCH THIS",
    "DON'T SKIP THIS",
]


def load_font(size):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_thumbnail_fallback(title):
    """Fallback: generate thumbnail using PIL (dark gradient + text)."""
    print(f"  Using fallback PIL thumbnail generator...")

    img  = Image.new("RGB", (THUMB_W, THUMB_H))
    draw = ImageDraw.Draw(img)

    # Dark gradient
    for y in range(THUMB_H):
        ratio = y / THUMB_H
        r = int(GRADIENT_TOP[0] + (GRADIENT_BOTTOM[0] - GRADIENT_TOP[0]) * ratio)
        g = int(GRADIENT_TOP[1] + (GRADIENT_BOTTOM[1] - GRADIENT_TOP[1]) * ratio)
        b = int(GRADIENT_TOP[2] + (GRADIENT_BOTTOM[2] - GRADIENT_TOP[2]) * ratio)
        draw.line([(0, y), (THUMB_W, y)], fill=(r, g, b))

    # Grid
    for x in range(0, THUMB_W, 120):
        draw.line([(x, 0), (x, THUMB_H)], fill=(20, 20, 40))
    for y_line in range(0, THUMB_H, 120):
        draw.line([(0, y_line), (THUMB_W, y_line)], fill=(20, 20, 40))

    font_large   = load_font(110)
    font_accent  = load_font(116)
    font_small   = load_font(32)
    font_tagline = load_font(36)

    # Split title
    clean = clean_title_for_thumbnail(title)
    words = clean.upper().split()

    if len(words) <= 4:
        line1, line2 = " ".join(words), ""
    else:
        mid = max(3, len(words) // 2 - 1) if len(words) > 6 else len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

    def draw_bordered(pos, text, font, fill, bw=4, anchor="mm"):
        x, y = pos
        for dx in range(-bw, bw + 1):
            for dy in range(-bw, bw + 1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=BLACK, anchor=anchor)
        draw.text(pos, text, font=font, fill=fill, anchor=anchor)

    if line2:
        draw_bordered((THUMB_W//2, THUMB_H//2 - 100), line1, font_large, WHITE)
        # Red accent bar
        bar_w = int(THUMB_W * 0.55)
        bar_x = (THUMB_W - bar_w) // 2
        draw.rectangle([(bar_x, THUMB_H//2 - 30), (bar_x + bar_w, THUMB_H//2 - 23)], fill=RED_ACCENT)
        draw_bordered((THUMB_W//2, THUMB_H//2 + 40), line2, font_accent, YELLOW, bw=5)
        # Tagline
        tagline = random.choice(THUMB_TAGLINES)
        draw_bordered((THUMB_W//2, THUMB_H//2 + 160), tagline, font_tagline, (255, 80, 80), bw=3)
    else:
        draw_bordered((THUMB_W//2, THUMB_H//2 - 30), line1, font_accent, YELLOW, bw=5)
        bar_w = int(THUMB_W * 0.55)
        bar_x = (THUMB_W - bar_w) // 2
        draw.rectangle([(bar_x, THUMB_H//2 + 50), (bar_x + bar_w, THUMB_H//2 + 57)], fill=RED_ACCENT)
        tagline = random.choice(THUMB_TAGLINES)
        draw_bordered((THUMB_W//2, THUMB_H//2 + 110), tagline, font_tagline, (255, 80, 80), bw=3)

    # Watermark
    draw_bordered((THUMB_W - 30, THUMB_H - 30), "@NEXTLEVELMIND", font_small,
                  (200, 200, 200), bw=2, anchor="rb")

    return img


def main():
    print("=" * 50)
    print("  Long-Form Thumbnail — Gemini AI + Fallback")
    print("=" * 50)

    if not os.path.exists("output/seo_data.json"):
        print("\n  ERROR: output/seo_data.json not found!")
        return

    with open("output/seo_data.json", encoding="utf-8") as f:
        seo = json.load(f)

    title = seo["youtube_title"]
    print(f"\n  Title: {title}")

    # Try Gemini first, fall back to PIL
    img = None
    if GEMINI_IMAGE_AVAILABLE:
        img = generate_thumbnail_gemini(title)

    if img is None:
        img = generate_thumbnail_fallback(title)

    img.save("output/thumbnail.jpg", quality=97, optimize=True)

    size_kb = os.path.getsize("output/thumbnail.jpg") // 1024
    print(f"\n  Saved: output/thumbnail.jpg ({size_kb} KB)")
    print("=" * 50)
    print("\n  Next step: Run long_07_upload.py")


if __name__ == "__main__":
    main()
