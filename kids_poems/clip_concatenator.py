"""
clip_concatenator.py — Clip Normalization & Concatenation for Kids Poems

Takes animated video clips (from Veo) or fallback image-to-video segments,
normalizes them to 1080x1920 @ 30fps, and concatenates with xfade transitions.
Replaces slideshow_builder.py when Veo is enabled.
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


def normalize_clip(clip_path, output_path, target_duration):
    """
    Normalize a video clip: upscale to 1080x1920, set 30fps,
    trim to target_duration, and ensure yuv420p format.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:flags=lanczos,"
            f"fps={VIDEO_FPS},setsar=1,format=yuv420p"
        ),
        "-t", f"{target_duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-an",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"    Normalize failed: {result.stderr[-300:]}")
        return None
    return output_path


def image_to_video_segment(image_path, output_path, duration):
    """
    Convert a static image into a video segment with Ken Burns effect.
    Used as a bridge when Veo fails for a verse and we fall back to a static image.
    """
    zoom_in = random.choice([True, False])
    zoom_expr = "1+0.03*t" if zoom_in else "1.12-0.03*t"
    x_expr = f"iw/2-(iw/({zoom_expr}))/2"
    y_expr = f"ih/2-(ih/({zoom_expr}))/2"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(duration),
        "-i", image_path,
        "-vf", (
            f"scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={int(duration * VIDEO_FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
            f"fps={VIDEO_FPS},"
            f"setsar=1,format=yuv420p"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-an",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"    Image-to-video failed: {result.stderr[-300:]}")
        return None
    return output_path


def concatenate_clips(clip_paths, output_path=None, timings=None, xfade_duration=None):
    """
    Concatenate video clips with xfade transitions.
    Normalizes each clip to target resolution/fps first, then chains with crossfade.
    """
    if not clip_paths:
        raise ValueError("No clips provided")

    output_path = output_path or os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    xfade_duration = xfade_duration or XFADE_DURATION

    n = len(clip_paths)
    norm_dir = os.path.join(OUTPUT_FOLDER, "clips_norm")
    os.makedirs(norm_dir, exist_ok=True)

    if timings and len(timings) == n:
        per_clip_durations = []
        for i, t in enumerate(timings):
            dur = t["end"] - t["start"]
            if i < n - 1 and i + 1 < len(timings):
                gap = timings[i + 1]["start"] - t["end"]
                dur += gap
            per_clip_durations.append(max(2.0, dur))
    else:
        per_clip_durations = [4.0] * n

    total = sum(per_clip_durations) - xfade_duration * max(0, n - 1)
    print(f"  Concatenating: {n} clips, ~{total:.1f}s total")

    norm_paths = []
    for i, clip in enumerate(clip_paths):
        norm_path = os.path.join(norm_dir, f"norm_{i:02d}.mp4")
        result = normalize_clip(clip, norm_path, per_clip_durations[i])
        if result:
            norm_paths.append(norm_path)
        else:
            print(f"    WARNING: Clip {i} normalization failed, using raw")
            norm_paths.append(clip)

    inputs = []
    filter_parts = []
    for i, norm in enumerate(norm_paths):
        inputs.extend(["-i", norm])
        filter_parts.append(f"[{i}:v]setsar=1,format=yuv420p[v{i}]")

    if n == 1:
        filter_complex = filter_parts[0].replace("[v0]", "[vout]")
    else:
        xfade_chain = list(filter_parts)
        prev = "v0"
        offset = per_clip_durations[0] - xfade_duration
        for i in range(1, n):
            out_label = "vout" if i == n - 1 else f"xf{i}"
            xfade_chain.append(
                f"[{prev}][v{i}]xfade=transition=fade:"
                f"duration={xfade_duration}:offset={offset:.3f}[{out_label}]"
            )
            prev = out_label
            if i < n - 1:
                offset += per_clip_durations[i] - xfade_duration
        filter_complex = ";\n".join(xfade_chain)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path,
        ]
    )

    print("  Running ffmpeg clip concatenation...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  FFmpeg stderr:\n{result.stderr[-500:]}")
        raise RuntimeError(f"Clip concatenation failed (exit {result.returncode})")

    duration = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Concatenated: {duration:.1f}s, {size_mb:.1f}MB")

    # Cleanup normalized clips
    for f in norm_paths:
        try:
            if os.path.exists(f) and norm_dir in f:
                os.remove(f)
        except PermissionError:
            pass

    return output_path


if __name__ == "__main__":
    clips_dir = os.path.join(OUTPUT_FOLDER, "clips")
    if os.path.isdir(clips_dir):
        clips = sorted([
            os.path.join(clips_dir, f)
            for f in os.listdir(clips_dir)
            if f.lower().endswith(".mp4")
        ])
        if clips:
            concatenate_clips(clips, target_duration=20)
        else:
            print("  No clips found in assets/output/clips/")
    else:
        print("  Run video_clip_generator.py first")
