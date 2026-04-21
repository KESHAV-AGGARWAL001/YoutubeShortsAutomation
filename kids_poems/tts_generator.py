"""
tts_generator.py — Voiceover Generator for Kids Poems

Uses Edge TTS with a warm, child-friendly voice.
Slower rate and higher pitch than adult content.
Adds silence gaps between poem lines for natural pacing.
"""

import os
import sys
import asyncio
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import OUTPUT_FOLDER, TTS_VOICE, TTS_RATE, TTS_PITCH

import edge_tts


async def _generate_line(text, output_file):
    """Generate TTS for a single line."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
    )
    await communicate.save(output_file)
    return os.path.exists(output_file) and os.path.getsize(output_file) > 500


def get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 0
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0))


def generate_silence(duration, output_path):
    """Generate a silence audio file of given duration."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration),
        "-c:a", "libmp3lame", "-q:a", "9",
        output_path,
    ], capture_output=True)


def generate_voiceover(poem_lines, output_path=None):
    """
    Generate voiceover from poem lines with pauses between lines.
    Returns the final merged voiceover path and per-line timing data.
    """
    output_path = output_path or os.path.join(OUTPUT_FOLDER, "voiceover.mp3")
    vo_dir = os.path.join(OUTPUT_FOLDER, "voiceovers")
    os.makedirs(vo_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"  Voice: {TTS_VOICE} | Rate: {TTS_RATE} | Pitch: {TTS_PITCH}")

    silence_gap = 0.6  # seconds between lines
    silence_file = os.path.join(vo_dir, "silence.mp3")
    generate_silence(silence_gap, silence_file)

    parts = []
    timings = []
    cursor = 0.0

    for i, line in enumerate(poem_lines):
        line_file = os.path.join(vo_dir, f"line_{i:02d}.mp3")
        print(f"    Line {i + 1}: \"{line[:50]}...\"" if len(line) > 50 else f"    Line {i + 1}: \"{line}\"")

        success = asyncio.run(_generate_line(line, line_file))
        if not success:
            print(f"    WARNING: TTS failed for line {i + 1}")
            continue

        dur = get_duration(line_file)
        timings.append({
            "index": i,
            "text": line,
            "start": round(cursor, 3),
            "end": round(cursor + dur, 3),
        })
        parts.append(line_file)
        cursor += dur

        # Add silence gap (except after last line)
        if i < len(poem_lines) - 1:
            parts.append(silence_file)
            cursor += silence_gap

    if not parts:
        raise RuntimeError("No voiceover lines generated")

    # Merge all parts into one file
    concat_file = os.path.join(vo_dir, "concat_list.txt")
    with open(concat_file, "w") as f:
        for p in parts:
            safe = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{safe}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
    ], capture_output=True)

    total_dur = get_duration(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Voiceover: {total_dur:.1f}s, {size_kb:.0f}KB")

    # Save timings for subtitle builder
    timings_file = os.path.join(OUTPUT_FOLDER, "line_timings.json")
    with open(timings_file, "w", encoding="utf-8") as f:
        json.dump(timings, f, indent=2)

    return output_path, total_dur, timings


def main():
    print("=" * 50)
    print("  Kids Poem TTS Generator")
    print("=" * 50)

    poem_file = os.path.join(OUTPUT_FOLDER, "poem_data.json")
    if not os.path.exists(poem_file):
        print("  ERROR: Run poem_generator.py first")
        return

    with open(poem_file, "r", encoding="utf-8") as f:
        poem_data = json.load(f)

    lines = poem_data.get("poem_lines", [])
    print(f"\n  Generating voiceover for {len(lines)} lines...")
    path, duration, timings = generate_voiceover(lines)

    print(f"\n  Duration: {duration:.1f}s")
    print("=" * 50)


if __name__ == "__main__":
    main()
