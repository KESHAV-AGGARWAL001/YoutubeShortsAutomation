"""
render_story_reels.py — Render Story Series Parts into Video Reels

Takes script.json for each part and renders a vertical 9:16 MP4 reel:
  1. Generate TTS narration using Edge TTS (free, no API key)
  2. Create video with dark gradient background
  3. Overlay hook text, part branding, watermark, and cliffhanger
  4. Compress to ~15MB

Usage:
  python render_story_reels.py --series {series_id}             # render all parts
  python render_story_reels.py --series {series_id} --part 2    # render specific part
  python render_story_reels.py --all                             # render all pending
"""

import os
import sys
import json
import glob
import time
import re
import asyncio
import argparse
import subprocess
import textwrap
import edge_tts
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SERIES_DIR = "story_series"
REGISTRY   = os.path.join(SERIES_DIR, "series_registry.json")

# TTS config — same as existing voiceover pipeline
VOICE = "en-US-GuyNeural"
RATE  = "-5%"
PITCH = "-3Hz"

# Video config
WIDTH  = 1080
HEIGHT = 1920

# Font search
FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
]


def get_font_path():
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            return fp
    return None


def escape_font_path(fp):
    fp = fp.replace("\\", "/")
    fp = re.sub(r"^([A-Za-z]):/", r"\1\\:/", fp)
    return fp


def get_duration(filepath):
    try:
        r = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ], capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def escape_drawtext(text):
    """Escape text for FFmpeg drawtext filter."""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")
    text = text.replace(":", "\\:")
    text = text.replace("%", "%%")
    return text


# ── TTS Generation ──────────────────────────────────────────────

async def generate_tts(text, output_path):
    """Generate voiceover using Edge TTS."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        pitch=PITCH
    )
    await communicate.save(output_path)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 1000


def create_narration(script_text, output_path):
    """Generate TTS narration for a part's script."""
    print(f"  Generating TTS narration...")
    print(f"    Voice: {VOICE} | Rate: {RATE} | Pitch: {PITCH}")

    start = time.time()
    success = asyncio.run(generate_tts(script_text, output_path))

    if success:
        duration = get_duration(output_path)
        size_kb  = os.path.getsize(output_path) // 1024
        print(f"  ✅ Narration: {duration:.1f}s ({size_kb}KB)")
        return duration
    else:
        print(f"  ❌ TTS generation failed!")
        return 0.0


# ── Video Rendering ─────────────────────────────────────────────

def create_dark_gradient_bg(duration, output_path):
    """Create a dark cinematic gradient background video."""
    vf = (
        f"color=c=#0a0a1a:s={WIDTH}x{HEIGHT}:d={duration}:r=30,"
        "format=yuv420p,"
        # Subtle animated gradient overlay
        "drawbox=x=0:y=0:w=iw:h=ih/3:color=#0f0f2e@0.4:t=fill,"
        "drawbox=x=0:y=ih*2/3:w=iw:h=ih/3:color=#1a0a1a@0.3:t=fill"
    )

    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#0a0a1a:s={WIDTH}x{HEIGHT}:d={duration}:r=30",
        "-vf", "format=yuv420p",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        output_path
    ], capture_output=True, text=True)

    if os.path.exists(output_path):
        return True
    print(f"  ❌ Background generation failed: {result.stderr[-500:]}")
    return False


def build_subtitle_entries(script_text, duration):
    """Split script into timed subtitle entries for drawtext."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    lines = []
    for sent in sentences:
        wrapped = textwrap.wrap(sent, width=25)
        lines.extend(wrapped)

    if not lines:
        return []

    line_dur = duration / len(lines)
    entries  = []
    for i, line in enumerate(lines):
        entries.append((
            round(i * line_dur, 3),
            round((i + 1) * line_dur, 3),
            line
        ))
    return entries


def render_reel(part_data, series_meta, narration_path, output_path):
    """
    Render a single story part into a vertical 9:16 reel video.

    Batched subtitle approach to avoid Windows 8191-char CLI limit.
    """
    font_path = get_font_path()
    font_part = f":fontfile='{escape_font_path(font_path)}'" if font_path else ""

    part_num    = part_data["part_number"]
    total_parts = series_meta["total_parts"]
    series_title = series_meta["series_title"]
    hook        = part_data.get("hook", "")
    cliffhanger = part_data.get("cliffhanger", "")
    script_text = part_data.get("script", "")

    narration_dur = get_duration(narration_path)
    if narration_dur <= 0:
        print(f"  ❌ Invalid narration duration")
        return False

    part_dir = os.path.dirname(output_path)
    os.makedirs(part_dir, exist_ok=True)

    print(f"  Rendering Part {part_num}/{total_parts}: {narration_dur:.1f}s")

    # ── Pass 1: Dark background + narration audio + base overlays ─────
    base_path = os.path.join(part_dir, "_base.mp4")

    # Build base filter with part branding
    hook_safe   = escape_drawtext(hook[:80])
    cliff_safe  = escape_drawtext(cliffhanger[:80])
    series_safe = escape_drawtext(series_title[:40])

    # Hook appears for first 4 seconds, cliffhanger in last 6
    hook_end   = min(4.0, narration_dur * 0.2)
    cliff_start = max(0, narration_dur - 6.0)

    # Next part text
    if part_num < total_parts:
        next_text = escape_drawtext(f"\U0001F447 Part {part_num + 1} tomorrow")
    else:
        next_text = escape_drawtext("Series Finale")

    vf_base = (
        "format=yuv420p,"
        # Dark gradient overlays
        "drawbox=x=0:y=0:w=iw:h=ih/4:color=#0f0f2e@0.3:t=fill,"
        "drawbox=x=0:y=ih*3/4:w=iw:h=ih/4:color=#1a0a1a@0.3:t=fill,"
        # TOP: Part X of Y — small, centered
        f"drawtext=text='PART {part_num} of {total_parts}'"
        f"{font_part}:fontsize=32:fontcolor=white@0.7"
        f":x=(w-text_w)/2:y=80,"
        # BOTTOM: @nextlevelmind_km watermark — always visible
        f"drawtext=text='@nextlevelmind_km'"
        f"{font_part}:fontsize=24:fontcolor=white@0.6"
        f":x=w-text_w-30:y=h-60"
    )

    # Add cliffhanger only if not last part (or always for finale text)
    if cliff_safe:
        vf_base += (
            f",drawtext=text='{cliff_safe}'"
            f"{font_part}:fontsize=42:fontcolor=white"
            f":bordercolor=black:borderw=3"
            f":x=(w-text_w)/2:y=(h/2)-60"
            f":enable='gte(t,{cliff_start})'"
        )

    # Next part / finale text
    vf_base += (
        f",drawtext=text='{next_text}'"
        f"{font_part}:fontsize=28:fontcolor=#FFD700"
        f":x=(w-text_w)/2:y=(h/2)+20"
        f":enable='gte(t,{cliff_start + 1.5})'"
    )

    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#0a0a1a:s={WIDTH}x{HEIGHT}:d={narration_dur}:r=30",
        "-i", narration_path,
        "-vf", vf_base,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(narration_dur),
        "-shortest",
        "-movflags", "+faststart",
        base_path
    ], capture_output=True, text=True)

    if not (os.path.exists(base_path) and os.path.getsize(base_path) > 10000):
        print(f"  ❌ Base pass failed: {result.stderr[-800:]}")
        return False

    print(f"  Base pass done ✓")

    # ── Pass 2+: Burn subtitle batches ────────────────────────────────
    subtitle_entries = build_subtitle_entries(script_text, narration_dur)

    if not subtitle_entries:
        os.replace(base_path, output_path)
        print(f"  No subtitles — reel saved ✓")
        return True

    # Center subtitles in middle third of frame
    center_y = int((HEIGHT - 56) / 2)  # fontsize 56

    BATCH = 8
    batches = [subtitle_entries[i:i+BATCH] for i in range(0, len(subtitle_entries), BATCH)]
    current = base_path

    print(f"  Burning {len(subtitle_entries)} subtitle entries in {len(batches)} batches...")

    for idx, batch in enumerate(batches, 1):
        next_file = os.path.join(part_dir, f"_pass{idx}.mp4")

        filters = []
        for t0, t1, text in batch:
            filters.append(
                f"drawtext=text='{escape_drawtext(text)}'"
                f"{font_part}:fontsize=56:fontcolor=white"
                f":bordercolor=black:borderw=4"
                f":x=(w-text_w)/2:y={center_y}"
                f":enable='between(t,{t0},{t1})'"
            )

        vf_chain = ",".join(filters)

        r = subprocess.run([
            "ffmpeg", "-y",
            "-i", current,
            "-vf", vf_chain,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            next_file
        ], capture_output=True, text=True)

        if not (os.path.exists(next_file) and os.path.getsize(next_file) > 10000):
            print(f"  ⚠️  Subtitle batch {idx} failed, using current state")
            break

        # Clean previous temp
        if current != base_path or idx > 1:
            try: os.remove(current)
            except Exception: pass
        current = next_file

    # Rename final to output
    if current != output_path:
        if os.path.exists(output_path):
            os.remove(output_path)
        os.replace(current, output_path)

    # Clean up any remaining temp files
    for tmp in glob.glob(os.path.join(part_dir, "_pass*.mp4")):
        try: os.remove(tmp)
        except Exception: pass
    for tmp in glob.glob(os.path.join(part_dir, "_base.mp4")):
        try: os.remove(tmp)
        except Exception: pass

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✅ Reel rendered: {size_mb:.1f}MB")
    return True


# ── Series Rendering ────────────────────────────────────────────

def render_series(series_id, part_num=None):
    """Render all (or specific) parts of a series."""
    series_dir = os.path.join(SERIES_DIR, series_id)
    meta_path  = os.path.join(series_dir, "series_meta.json")

    if not os.path.exists(meta_path):
        print(f"  ❌ Series not found: {series_id}")
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    total_parts = meta["total_parts"]
    print(f"\n  📖 Series: {meta['series_title']}")
    print(f"  Parts: {total_parts} | Category: {meta['category']}")

    # Determine which parts to render
    if part_num:
        parts_to_render = [part_num]
    else:
        parts_to_render = list(range(1, total_parts + 1))

    results = {}
    for pn in parts_to_render:
        part_dir    = os.path.join(series_dir, f"part_{pn}")
        script_path = os.path.join(part_dir, "script.json")
        reel_path   = os.path.join(part_dir, "reel.mp4")
        narr_path   = os.path.join(part_dir, "narration.mp3")

        print(f"\n  {'─' * 45}")
        print(f"  Part {pn}/{total_parts}")
        print(f"  {'─' * 45}")

        if not os.path.exists(script_path):
            print(f"  ❌ script.json not found at {script_path}")
            results[pn] = False
            continue

        # Skip if reel already exists
        if os.path.exists(reel_path) and os.path.getsize(reel_path) > 100000:
            size_mb = os.path.getsize(reel_path) / (1024 * 1024)
            print(f"  ⏭️  Already rendered ({size_mb:.1f}MB) — skipping")
            results[pn] = True
            continue

        with open(script_path, "r", encoding="utf-8") as f:
            part_data = json.load(f)

        script_text = part_data.get("script", "")
        if not script_text:
            print(f"  ❌ Empty script for part {pn}")
            results[pn] = False
            continue

        word_count = len(script_text.split())
        print(f"  Title: {part_data.get('title', f'Part {pn}')}")
        print(f"  Mood:  {part_data.get('mood', '?')}")
        print(f"  Words: {word_count}")

        # Step 1: Generate TTS narration
        if not os.path.exists(narr_path) or os.path.getsize(narr_path) < 1000:
            duration = create_narration(script_text, narr_path)
            if duration <= 0:
                print(f"  ❌ TTS failed for part {pn}")
                results[pn] = False
                continue
        else:
            duration = get_duration(narr_path)
            print(f"  Narration exists: {duration:.1f}s")

        # Step 2: Render video
        success = render_reel(part_data, meta, narr_path, reel_path)
        results[pn] = success

    # Summary
    print(f"\n  {'═' * 45}")
    print(f"  Render Summary: {meta['series_title']}")
    print(f"  {'═' * 45}")
    for pn, ok in results.items():
        status = "✅ Done" if ok else "❌ Failed"
        print(f"  Part {pn}: {status}")

    return all(results.values())


def render_all_pending():
    """Render all parts for all active series that have pending renders."""
    if not os.path.exists(REGISTRY):
        print("  No series registry found. Generate a story first.")
        return

    with open(REGISTRY, "r", encoding="utf-8") as f:
        registry = json.load(f)

    active = registry.get("active_series", [])
    if not active:
        print("  No active series to render.")
        return

    print(f"\n  Found {len(active)} active series")

    for series_info in active:
        sid = series_info["series_id"]
        print(f"\n{'=' * 55}")
        render_series(sid)


# ── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Render story series reels")
    parser.add_argument("--series", type=str,           help="Series ID to render")
    parser.add_argument("--part",   type=int,           help="Specific part number")
    parser.add_argument("--all",    action="store_true", help="Render all pending series")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  🎬 Story Reel Renderer — NextLevelMind")
    print(f"  TTS: {VOICE} | Resolution: {WIDTH}x{HEIGHT}")
    print("=" * 55)

    if args.all:
        render_all_pending()
    elif args.series:
        success = render_series(args.series, part_num=args.part)
        if success:
            print(f"\n  Next: python schedule_story_upload.py")
        else:
            print(f"\n  ⚠️  Some parts failed — check errors above")
            sys.exit(1)
    else:
        print("\n  Usage:")
        print("    python render_story_reels.py --series {series_id}")
        print("    python render_story_reels.py --series {id} --part 2")
        print("    python render_story_reels.py --all")

        # Show available series
        if os.path.exists(REGISTRY):
            with open(REGISTRY, "r") as f:
                reg = json.load(f)
            active = reg.get("active_series", [])
            if active:
                print(f"\n  Available series:")
                for s in active:
                    print(f"    {s['series_id']} ({s['total_parts']} parts)")
        sys.exit(1)


if __name__ == "__main__":
    main()
