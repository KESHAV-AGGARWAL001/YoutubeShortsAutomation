"""
slideshow_builder.py — Animated Slideshow from AI-Generated Images

Creates a Ken Burns (zoom/pan) slideshow from the per-verse images.
Each image maps to one poem line — duration synced to voiceover timing.
"""

import os
import sys
import subprocess
import random
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    OUTPUT_FOLDER, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, XFADE_DURATION,
)


def _get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 0
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0))


def build_slideshow(image_paths, output_path=None, target_duration=None, timings=None):
    """
    Build a silent slideshow video from images with Ken Burns zoom + xfade.
    If timings provided, each image duration matches its poem line duration.
    """
    if not image_paths:
        raise ValueError("No images provided")

    output_path = output_path or os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    n = len(image_paths)

    # Calculate per-image duration
    if timings and len(timings) == n:
        # Match each image to its poem line duration + gap
        per_image_durations = []
        for i, t in enumerate(timings):
            dur = t["end"] - t["start"]
            if i < n - 1 and i + 1 < len(timings):
                gap = timings[i + 1]["start"] - t["end"]
                dur += gap
            per_image_durations.append(max(2.0, dur))
    elif target_duration:
        total_xfade = XFADE_DURATION * max(0, n - 1)
        available = target_duration + total_xfade
        per_img = max(2.0, available / n)
        per_image_durations = [per_img] * n
    else:
        per_image_durations = [4.0] * n

    total = sum(per_image_durations) - XFADE_DURATION * max(0, n - 1)
    print(f"  Slideshow: {n} images, {total:.1f}s total")

    inputs = []
    filter_parts = []

    for i, img_path in enumerate(image_paths):
        dur = per_image_durations[i]
        inputs.extend(["-loop", "1", "-t", str(dur), "-i", img_path])

        # Ken Burns: gentle zoom in or out
        zoom_in = random.choice([True, False])
        if zoom_in:
            zoom_expr = "1+0.03*t"
        else:
            zoom_expr = "1.12-0.03*t"
        x_expr = f"iw/2-(iw/({zoom_expr}))/2"
        y_expr = f"ih/2-(ih/({zoom_expr}))/2"

        filter_parts.append(
            f"[{i}:v]scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={int(dur * VIDEO_FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
            f"fps={VIDEO_FPS},"
            f"setsar=1,format=yuv420p[v{i}]"
        )

    # Chain xfade transitions
    if n == 1:
        filter_complex = filter_parts[0].replace("[v0]", "[vout]")
    else:
        xfade_chain = list(filter_parts)
        prev = "v0"
        offset = per_image_durations[0] - XFADE_DURATION
        for i in range(1, n):
            out_label = "vout" if i == n - 1 else f"xf{i}"
            xfade_chain.append(
                f"[{prev}][v{i}]xfade=transition=fade:"
                f"duration={XFADE_DURATION}:offset={offset:.3f}[{out_label}]"
            )
            prev = out_label
            if i < n - 1:
                offset += per_image_durations[i] - XFADE_DURATION

        filter_complex = ";\n".join(xfade_chain)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path,
        ]
    )

    print("  Running ffmpeg slideshow build...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  FFmpeg stderr:\n{result.stderr[-500:]}")
        raise RuntimeError(f"Slideshow build failed (exit {result.returncode})")

    duration = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Slideshow: {duration:.1f}s, {size_mb:.1f}MB")

    return output_path


if __name__ == "__main__":
    images_dir = os.path.join(OUTPUT_FOLDER, "images")
    if os.path.isdir(images_dir):
        imgs = sorted([
            os.path.join(images_dir, f)
            for f in os.listdir(images_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ])
        if imgs:
            build_slideshow(imgs, target_duration=20)
        else:
            print("  No images found in assets/output/images/")
    else:
        print("  Run image_generator.py first")
