import os
import json
import random
import subprocess
from dotenv import load_dotenv
load_dotenv()

STOCK_FOLDER = "stock"
CLIPS_FOLDER = "output/clips"


def scan_all_clips():
    """Scan stock/ and return all clips from all subfolders"""
    if not os.path.exists(STOCK_FOLDER):
        os.makedirs(STOCK_FOLDER, exist_ok=True)
        return {}

    categories = {}
    for folder in os.listdir(STOCK_FOLDER):
        folder_path = os.path.join(STOCK_FOLDER, folder)
        if not os.path.isdir(folder_path):
            continue

        clips = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".mp4")
            and os.path.getsize(os.path.join(folder_path, f)) > 100000
        ]
        if clips:
            categories[folder] = clips

    return categories


def pick_one_clip(categories):
    """
    Pick a single random clip from a random category.
    This clip will loop for the entire video — consistent background.
    """
    available = list(categories.keys())
    chosen_category = random.choice(available)
    chosen_clip = random.choice(categories[chosen_category])
    return chosen_category, chosen_clip


def get_clip_duration(filepath):
    """Get duration of a video clip in seconds using ffprobe"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ], capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except Exception:
        return 10.0


def get_voiceover_duration():
    """Get total voiceover duration"""
    voiceover_dir = "output/voiceovers"
    if not os.path.exists(voiceover_dir):
        return 180.0

    total = 0.0
    for f in sorted(os.listdir(voiceover_dir)):
        if f.endswith(".mp3"):
            total += get_clip_duration(os.path.join(voiceover_dir, f))

    return total if total > 0 else 180.0


def get_section_timings():
    """
    Calculate the start time of each voiceover section so that subtitle
    text can be timed exactly to match when each section is spoken.
    Returns list of {name, text, start, end} dicts.
    """
    voiceover_dir = "output/voiceovers"
    sections_dir  = "output/sections"

    timings = []
    cursor  = 0.0

    section_files = sorted([
        f for f in os.listdir(voiceover_dir) if f.endswith(".mp3")
    ])

    for mp3_file in section_files:
        name = mp3_file.replace(".mp3", "")
        txt_file = os.path.join(sections_dir, f"{name}.txt")

        dur = get_clip_duration(os.path.join(voiceover_dir, mp3_file))

        text = ""
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read().strip()

        timings.append({
            "name":  name,
            "text":  text,
            "start": cursor,
            "end":   cursor + dur
        })
        cursor += dur

    return timings


def main():
    print("=" * 50)
    print("  Footage Manager — Black Background Mode")
    print("=" * 50)

    os.makedirs(CLIPS_FOLDER, exist_ok=True)

    # User requested plain black backgrounds instead of stock videos!
    print("\n  Skipping stock footage scanning (using solid black video).")

    # Save for thumbnail + video assembler
    with open("output/video_theme.json", "w") as f:
        json.dump({
            "categories":    ["black"],
            "selected_clip": "black_screen"
        }, f, indent=2)

    # Get voiceover duration
    print(f"\n  Checking voiceover duration...")
    required = get_voiceover_duration()
    print(f"  Required: {required:.1f}s ({required/60:.1f} mins)")

    # Calculate section timings (used by video assembler for subtitles)
    print(f"\n  Calculating subtitle timings...")
    timings = get_section_timings()
    with open("output/section_timings.json", "w") as f:
        json.dump(timings, f, indent=2, ensure_ascii=False)

    for t in timings:
        words = len(t["text"].split())
        print(f"    {t['name']}: {t['start']:.1f}s → {t['end']:.1f}s  ({words} words)")

    print("\n" + "=" * 50)
    print(f"  Done!")
    print(f"  Background: Pure Black Video")
    print("=" * 50)
    print("\n  Next step: Run 05_make_video.py")


if __name__ == "__main__":
    main()