import os
import json
import random
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
load_dotenv()

STOCK_FOLDER = "stock"


def get_background_from_stock():
    """
    Pick a random frame from today's chosen stock categories.
    Uses video_theme.json to know which 2 categories were selected.
    Falls back to any stock image if theme file missing.
    """
    # Load today's chosen categories
    theme_file = "output/video_theme.json"
    chosen_cats = []

    if os.path.exists(theme_file):
        with open(theme_file) as f:
            chosen_cats = json.load(f).get("categories", [])

    # Scan stock folder for JPG/PNG images
    # If no images, extract a frame from a video clip
    image_extensions = (".jpg", ".jpeg", ".png")
    images = []

    scan_folders = chosen_cats if chosen_cats else (
        [d for d in os.listdir(STOCK_FOLDER)
         if os.path.isdir(os.path.join(STOCK_FOLDER, d))]
        if os.path.exists(STOCK_FOLDER) else []
    )

    for cat in scan_folders:
        cat_path = os.path.join(STOCK_FOLDER, cat)
        if not os.path.isdir(cat_path):
            continue
        for f in os.listdir(cat_path):
            if f.lower().endswith(image_extensions):
                images.append(os.path.join(cat_path, f))

    if images:
        chosen = random.choice(images)
        print(f"  Background: {chosen}")
        return Image.open(chosen).convert("RGB")

    # No images — extract frame from a random stock video
    return extract_video_frame(scan_folders)


def extract_video_frame(scan_folders):
    """Extract a single frame from a stock video clip using FFmpeg"""
    import subprocess
    import tempfile

    video_path = None

    for cat in scan_folders:
        cat_path = os.path.join(STOCK_FOLDER, cat)
        if not os.path.isdir(cat_path):
            continue
        for f in os.listdir(cat_path):
            if f.lower().endswith(".mp4"):
                video_path = os.path.join(cat_path, f)
                break
        if video_path:
            break

    if not video_path:
        print("  No stock files found — using gradient background")
        return create_gradient_background()

    print(f"  Extracting frame from: {os.path.basename(video_path)}")

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    subprocess.run([
        "ffmpeg", "-y",
        "-ss", "00:00:03",      # grab frame at 3 seconds in
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        tmp_path
    ], capture_output=True)

    if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 1000:
        img = Image.open(tmp_path).convert("RGB")
        os.unlink(tmp_path)
        return img

    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
    return create_gradient_background()


def create_gradient_background():
    """Create a simple dark gradient as last resort"""
    W, H = 1280, 720
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        shade = int(20 + (y / H) * 40)
        draw.line([(0, y), (W, y)], fill=(shade, shade, shade + 10))
    return img


def add_overlay(img):
    """Add a semi-transparent overlay to make text readable"""
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 100))
    base    = img.convert("RGBA")
    merged  = Image.alpha_composite(base, overlay)
    return merged.convert("RGB")


def add_text_black(img, title):
    """
    Add bold BLACK text to thumbnail.
    Black text on bright nature footage looks clean and professional.
    """
    draw         = ImageDraw.Draw(img)
    W, H         = img.size

    # Load fonts
    font_large = None
    font_small = None
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_large = ImageFont.truetype(fp, 85)
                font_small = ImageFont.truetype(fp, 38)
                break
            except Exception:
                continue

    if font_large is None:
        font_large = ImageFont.load_default()
        font_small = font_large

    # Shorten title — max 6 words for thumbnail
    words     = title.upper().split()[:6]
    mid       = len(words) // 2
    line1     = " ".join(words[:mid])
    line2     = " ".join(words[mid:])

    # White shadow offset for depth (behind black text)
    for offset in [(3, 3), (2, 2)]:
        draw.text(
            (W//2 + offset[0], H//2 - 55 + offset[1]),
            line1, font=font_large, fill=(255, 255, 255, 180), anchor="mm"
        )
        draw.text(
            (W//2 + offset[0], H//2 + 55 + offset[1]),
            line2, font=font_large, fill=(255, 255, 255, 180), anchor="mm"
        )

    # Main BLACK text
    draw.text(
        (W//2, H//2 - 55), line1,
        font=font_large, fill=(0, 0, 0), anchor="mm"
    )
    draw.text(
        (W//2, H//2 + 55), line2,
        font=font_large, fill=(0, 0, 0), anchor="mm"
    )

    # Black accent line under text
    draw.rectangle(
        [(W//2 - 180, H//2 + 110), (W//2 + 180, H//2 + 114)],
        fill=(0, 0, 0)
    )

    return img


def main():
    print("=" * 50)
    print("  Thumbnail Generator — Stock Background")
    print("  Text color: Black")
    print("=" * 50)

    with open("output/seo_data.json") as f:
        seo = json.load(f)

    title = seo["youtube_title"]
    print(f"\n  Title: {title}")

    # Get background from stock footage
    print("\n  Getting background from stock library...")
    bg = get_background_from_stock()

    # Resize to YouTube thumbnail dimensions
    bg = bg.resize((1280, 720), Image.LANCZOS)

    # Add light overlay so black text is readable
    print("  Adding overlay for text contrast...")
    bg = add_overlay(bg)

    # Add black text
    print("  Adding black title text...")
    bg = add_text_black(bg, title)

    # Save
    bg.save("output/thumbnail.jpg", quality=95)

    print("\n" + "=" * 50)
    print("  Done! Thumbnail saved: output/thumbnail.jpg")
    print("  Size: 1280x720")
    print("  Text: Black on stock footage background")
    print("=" * 50)
    print("\n  Next step: Run 07_upload.py")


if __name__ == "__main__":
    main()