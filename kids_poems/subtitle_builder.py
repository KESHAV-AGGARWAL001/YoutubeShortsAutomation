"""
subtitle_builder.py — Karaoke-Style Subtitles for Kids Poems

Creates large, colorful, word-by-word subtitles that help kids
follow along and learn to read. Each word highlights as it's spoken.
"""

import os
import sys
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import OUTPUT_FOLDER


def seconds_to_srt(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def build_srt(timings, output_path=None):
    """
    Build SRT subtitle file from line timings.
    Shows one poem line at a time, large and centered.
    """
    output_path = output_path or os.path.join(OUTPUT_FOLDER, "subtitles.srt")
    counter = 1

    with open(output_path, "w", encoding="utf-8") as f:
        for t in timings:
            text = t["text"].strip()
            if not text:
                continue

            start = seconds_to_srt(t["start"])
            end = seconds_to_srt(t["end"])

            f.write(f"{counter}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n")
            f.write("\n")
            counter += 1

    print(f"  SRT: {counter - 1} subtitle entries")
    return output_path


def get_subtitle_filter(srt_path, font_path=None):
    """
    Build FFmpeg subtitle filter string for burning colorful subtitles.
    Uses large, bold text with bright colors — perfect for kids.
    """
    srt_escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")

    # Kid-friendly font setup
    font_spec = ""
    if font_path and os.path.exists(font_path):
        fp = font_path.replace("\\", "/")
        fp = re.sub(r"^([A-Za-z]):/", r"\1\\:/", fp)
        font_spec = f"FontName={os.path.splitext(os.path.basename(font_path))[0]},"
    else:
        font_spec = "FontName=Arial,"

    style = (
        f"{font_spec}"
        f"FontSize=20,"
        f"PrimaryColour=&H0000DDFF,"  # Yellow (BGR format)
        f"OutlineColour=&H00000000,"  # Black outline
        f"BackColour=&H80000000,"     # Semi-transparent background
        f"Outline=3,"
        f"Shadow=1,"
        f"MarginV=120,"              # Higher from bottom for kids
        f"Alignment=2,"              # Bottom center
        f"Bold=1"
    )

    return f"subtitles='{srt_escaped}':force_style='{style}'"


def main():
    print("=" * 50)
    print("  Kids Poem Subtitle Builder")
    print("=" * 50)

    timings_file = os.path.join(OUTPUT_FOLDER, "line_timings.json")
    if not os.path.exists(timings_file):
        print("  ERROR: Run tts_generator.py first")
        return

    with open(timings_file, "r", encoding="utf-8") as f:
        timings = json.load(f)

    srt_path = build_srt(timings)
    print(f"  Saved: {srt_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
