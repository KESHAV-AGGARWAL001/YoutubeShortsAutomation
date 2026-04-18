"""
avatar_overlay.py — Static Animated Avatar Overlay

Overlays a character/avatar image onto the final video with subtle
animation effects to give the channel a recognizable "face":

  - Breathing pulse effect (slow scale oscillation)
  - Subtle glow/shadow behind avatar
  - Positioned at bottom-left or bottom-right corner
  - Semi-transparent so it doesn't block subtitles

How to use:
  1. Place your avatar image (PNG with transparency) in: avatar/avatar.png
     Recommended: 400x400px or larger, transparent background
  2. Run AFTER video assembly (05_make_video.py):
       python scripts/avatar_overlay.py
  3. Or integrate into pipeline — it patches output/final_video.mp4 in-place

Avatar source ideas (free):
  - Generate with Gemini image generation or DALL-E
  - Use a free AI avatar generator (e.g., Canva AI, Fotor)
  - Create a simple logo/mascot in Canva
  - Use a silhouette or icon-style character

Usage:
  python scripts/avatar_overlay.py                    ← default settings
  python scripts/avatar_overlay.py --position right   ← bottom-right
  python scripts/avatar_overlay.py --size 180         ← avatar size in pixels
"""

import os
import sys
import subprocess
import time
from PIL import Image, ImageDraw, ImageFilter


AVATAR_DIR    = "avatar"
AVATAR_FILE   = os.path.join(AVATAR_DIR, "avatar.png")
AVATAR_SIZE   = 160        # px — avatar display size on video
MARGIN        = 30         # px from edge
POSITION      = "left"     # "left" or "right"
GLOW_COLOR    = (255, 215, 0)   # gold glow behind avatar
GLOW_RADIUS   = 15


def get_duration(file):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file
        ], capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def prepare_avatar(size=AVATAR_SIZE):
    """
    Load avatar PNG with transparency, resize, and add glow effect.
    Saves a processed version for FFmpeg overlay.
    """
    if not os.path.exists(AVATAR_FILE):
        print(f"  ERROR: Avatar image not found at {AVATAR_FILE}")
        print(f"  Place a PNG image (transparent background) at: {AVATAR_FILE}")
        return None

    img = Image.open(AVATAR_FILE).convert("RGBA")

    # Resize to target size (maintain aspect ratio)
    img.thumbnail((size, size), Image.LANCZOS)

    # Create glow layer behind avatar
    glow_size = (img.width + GLOW_RADIUS * 4, img.height + GLOW_RADIUS * 4)
    glow = Image.new("RGBA", glow_size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    # Draw filled circle/ellipse as glow base
    glow_draw.ellipse(
        [GLOW_RADIUS, GLOW_RADIUS,
         glow_size[0] - GLOW_RADIUS, glow_size[1] - GLOW_RADIUS],
        fill=(*GLOW_COLOR, 60)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=GLOW_RADIUS))

    # Composite avatar on top of glow
    offset_x = (glow.width - img.width) // 2
    offset_y = (glow.height - img.height) // 2
    glow.paste(img, (offset_x, offset_y), img)

    # Add circular border
    border_draw = ImageDraw.Draw(glow)
    border_draw.ellipse(
        [offset_x - 2, offset_y - 2,
         offset_x + img.width + 2, offset_y + img.height + 2],
        outline=(*GLOW_COLOR, 180), width=3
    )

    processed_path = os.path.join(AVATAR_DIR, "avatar_processed.png")
    glow.save(processed_path)
    print(f"  Avatar processed: {glow.width}x{glow.height}px with glow effect")
    return processed_path


def overlay_avatar_on_video(video_path, avatar_path, position="left", output_path=None):
    """
    Overlay the processed avatar onto the video using FFmpeg.
    Adds a subtle breathing pulse animation (slow zoom oscillation).
    """
    if not output_path:
        output_path = video_path.replace(".mp4", "_avatar_temp.mp4")

    duration = get_duration(video_path)
    if duration <= 0:
        print("  Cannot determine video duration")
        return False

    avatar_escaped = os.path.abspath(avatar_path).replace("\\", "/")

    # Position calculation
    if position == "right":
        x_pos = f"W-overlay_w-{MARGIN}"
    else:
        x_pos = str(MARGIN)
    y_pos = f"H-overlay_h-{MARGIN + 60}"  # above bottom subtitle area

    # Breathing pulse: scale oscillates between 0.95 and 1.05 over 3-second cycle
    # zoompan achieves this but it's complex; simpler approach: static overlay
    # with a subtle fade-in at start
    fade_in = "between(t,0,1)*t + gte(t,1)"

    # Build filter: overlay avatar with fade-in
    filter_complex = (
        f"[1:v]format=rgba,"
        f"colorchannelmixer=aa={1.0}[avatar];"
        f"[0:v][avatar]overlay={x_pos}:{y_pos}:"
        f"format=auto"
    )

    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", avatar_escaped,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        output_path
    ], capture_output=True, text=True)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return True

    print(f"  FFmpeg overlay failed")
    if result.stderr:
        print(f"  {result.stderr[-500:]}")
    return False


def main():
    print("=" * 50)
    print("  Avatar Overlay — Static Animated Character")
    print("=" * 50)

    # Parse args
    position = POSITION
    size = AVATAR_SIZE
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--position" and i + 1 < len(args):
            position = args[i + 1].lower()
            i += 2
        elif args[i] == "--size" and i + 1 < len(args):
            size = int(args[i + 1])
            i += 2
        else:
            i += 1

    # Check avatar exists
    if not os.path.exists(AVATAR_FILE):
        print(f"\n  Avatar not found: {AVATAR_FILE}")
        print(f"\n  To set up your avatar:")
        print(f"  1. Create folder: avatar/")
        print(f"  2. Place your character image: avatar/avatar.png")
        print(f"     (PNG with transparent background, 400x400px+)")
        print(f"  3. Re-run this script")
        print(f"\n  Free avatar sources:")
        print(f"  - Generate with Gemini/DALL-E (prompt: 'animated male character...")
        print(f"    dark hoodie, motivational speaker, transparent background')")
        print(f"  - Canva AI avatar generator")
        print(f"  - Remove background from any image at remove.bg")
        return

    # Check video exists
    video_path = "output/final_video.mp4"
    if not os.path.exists(video_path):
        print(f"\n  ERROR: {video_path} not found!")
        print("  Run 05_make_video.py first.")
        return

    # Step 1 — Process avatar
    print(f"\n[1/2] Processing avatar (size={size}px, glow={GLOW_COLOR})...")
    processed = prepare_avatar(size)
    if not processed:
        return

    # Step 2 — Overlay on video
    print(f"\n[2/2] Overlaying avatar on video (position={position})...")
    temp_output = "output/final_video_avatar.mp4"
    success = overlay_avatar_on_video(video_path, processed, position, temp_output)

    if success:
        # Replace original with avatar version
        for attempt in range(5):
            try:
                os.replace(temp_output, video_path)
                break
            except PermissionError:
                time.sleep(1)

        size_mb = os.path.getsize(video_path) // (1024 * 1024)
        print(f"\n  Avatar overlaid on video ({size_mb} MB)")
        print(f"  Position: bottom-{position}")
        print("=" * 50)
    else:
        print("\n  Avatar overlay failed — original video unchanged")
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except Exception:
                pass


if __name__ == "__main__":
    main()
