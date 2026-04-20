"""
Radha Krishna YouTube Channel — Video Pipeline

Usage:  python main.py
Reads content/today_script.txt, builds a slideshow with voiceover,
and uploads to YouTube.

Script format (today_script.txt):
  Line 1: Video title
  Line 2: Video description
  Line 3+: Script content (spoken by TTS)
  Last few lines starting with #: Tags (optional)
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONTENT_FILE, OUTPUT_FOLDER
from image_picker import pick_random_images
from slideshow_builder import build_slideshow
from tts_generator import generate_voiceover, get_voiceover_duration
from video_compositor import composite_video
from youtube_uploader import upload_video


def parse_content_file(filepath):
    """
    Parse today_script.txt:
      Line 1 → title
      Line 2 → description
      Lines starting with # at the end → tags
      Everything else → script body
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Content file not found: {filepath}\n"
            "Create content/today_script.txt with your script."
        )

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    lines = [l for l in lines if l]

    if len(lines) < 3:
        raise ValueError(
            "Content file must have at least 3 lines:\n"
            "  Line 1: Title\n"
            "  Line 2: Description\n"
            "  Line 3+: Script content"
        )

    title = lines[0]
    description = lines[1]

    tags = []
    script_lines = []
    tag_section = False

    for line in reversed(lines[2:]):
        if line.startswith("#"):
            tags.insert(0, line.lstrip("#").strip())
            tag_section = True
        elif tag_section:
            break
        else:
            break

    tag_count = len(tags)
    script_lines = lines[2:] if tag_count == 0 else lines[2:-tag_count]
    script_body = "\n".join(script_lines)

    if not tags:
        tags = [
            "Radha Krishna", "राधा कृष्ण", "Bhagavad Gita",
            "भगवद्गीता", "Krishna", "Spirituality", "Hindi",
            "Devotional", "Geeta Saar", "गीता सार",
        ]

    return title, description, script_body, tags


def main():
    start_time = time.time()
    print("=" * 55)
    print("  Radha Krishna YouTube Pipeline")
    print("=" * 55)

    # ── Step 1: Read content ──────────────────────────
    print("\n[Step 1/6] Reading content...")
    title, description, script, tags = parse_content_file(CONTENT_FILE)
    print(f"  Title: {title}")
    print(f"  Script: {len(script)} chars, {len(script.split())} words")
    print(f"  Tags: {len(tags)} tags")
    print("  Done ✓")

    # ── Step 2: Pick images ───────────────────────────
    print("\n[Step 2/6] Picking images...")
    images = pick_random_images()
    print("  Done ✓")

    # ── Step 3: Generate voiceover ────────────────────
    print("\n[Step 3/6] Generating voiceover...")
    voiceover_path = os.path.join(OUTPUT_FOLDER, "voiceover.mp3")
    generate_voiceover(script, voiceover_path)
    vo_duration = get_voiceover_duration(voiceover_path)
    print(f"  Duration: {vo_duration:.1f}s")
    print("  Done ✓")

    # ── Step 4: Build slideshow ───────────────────────
    print("\n[Step 4/6] Building slideshow...")
    slideshow_path = os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    build_slideshow(images, slideshow_path, target_duration=vo_duration)
    print("  Done ✓")

    # ── Step 5: Composite final video ─────────────────
    print("\n[Step 5/6] Compositing final video...")
    final_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")
    composite_video(slideshow_path, voiceover_path, final_path)
    print("  Done ✓")

    # ── Step 6: Upload to YouTube ─────────────────────
    print("\n[Step 6/6] Uploading to YouTube...")
    full_description = f"{description}\n\n" + " ".join(f"#{t}" for t in tags[:10])
    video_id = upload_video(final_path, title, full_description, tags)
    print("  Done ✓")

    # ── Summary ───────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "=" * 55)
    print(f"  Pipeline complete in {elapsed:.0f}s")
    print(f"  Video: https://youtube.com/watch?v={video_id}")
    print("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)
