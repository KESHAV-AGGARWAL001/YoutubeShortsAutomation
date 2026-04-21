"""
video_compositor.py — Final Video Assembly for Kids Poems

Merges:
  1. Slideshow (Ken Burns images) + voiceover + background music
  2. Burns colorful subtitles onto the video
  3. Outputs final_video.mp4 ready for YouTube upload
"""

import os
import sys
import subprocess
import random
import json
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    OUTPUT_FOLDER, MUSIC_FOLDER, MUSIC_VOLUME,
    CATEGORY_MUSIC_MOOD,
)
from subtitle_builder import build_srt, get_subtitle_filter


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


def _pick_music(category=None):
    """Pick a random music track matching the poem's mood."""
    mood = CATEGORY_MUSIC_MOOD.get(category, "playful")
    mood_dir = os.path.join(MUSIC_FOLDER, mood)

    # Try mood-specific folder first
    if os.path.isdir(mood_dir):
        tracks = [
            os.path.join(mood_dir, f)
            for f in os.listdir(mood_dir)
            if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))
        ]
        if tracks:
            chosen = random.choice(tracks)
            print(f"  Music: {os.path.basename(chosen)} (mood: {mood})")
            return chosen

    # Fallback: any track in music/ root
    if os.path.isdir(MUSIC_FOLDER):
        all_tracks = []
        for root, dirs, files in os.walk(MUSIC_FOLDER):
            for f in files:
                if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg")):
                    all_tracks.append(os.path.join(root, f))
        if all_tracks:
            chosen = random.choice(all_tracks)
            print(f"  Music: {os.path.basename(chosen)} (random fallback)")
            return chosen

    print("  No music found — video will have voiceover only")
    return None


def composite_video(slideshow_path, voiceover_path, output_path=None,
                    category=None, timings=None):
    """
    Full video assembly:
    1. Merge slideshow + voiceover + music → video_no_subs.mp4
    2. Burn subtitles → final_video.mp4
    """
    output_path = output_path or os.path.join(OUTPUT_FOLDER, "final_video.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    vo_duration = _get_duration(voiceover_path)
    print(f"  Voiceover: {vo_duration:.1f}s")

    music_file = _pick_music(category)

    # ── Step 1: Merge slideshow + audio ─────────────────
    no_subs = os.path.join(OUTPUT_FOLDER, "video_no_subs.mp4")

    if music_file:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", slideshow_path,
            "-i", voiceover_path,
            "-stream_loop", "-1", "-i", music_file,
            "-filter_complex",
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume={MUSIC_VOLUME}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-t", str(vo_duration + 1.0),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            no_subs,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", slideshow_path,
            "-i", voiceover_path,
            "-map", "0:v",
            "-map", "1:a",
            "-t", str(vo_duration + 1.0),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            no_subs,
        ]

    print("  Compositing video + audio...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  FFmpeg stderr:\n{result.stderr[-500:]}")
        raise RuntimeError("Video compositing failed")

    size_mb = os.path.getsize(no_subs) / (1024 * 1024)
    print(f"  Video (no subs): {size_mb:.1f}MB")

    # ── Step 2: Burn subtitles ──────────────────────────
    if timings:
        print("  Building subtitles...")
        srt_path = build_srt(timings)
        vf = get_subtitle_filter(srt_path)

        print("  Burning subtitles onto video...")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", no_subs,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "copy",
            output_path,
        ], capture_output=True, text=True, timeout=600)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  Final video (with subs): {size_mb:.1f}MB")
        else:
            print("  Subtitle burn failed — using video without subs")
            shutil.copy2(no_subs, output_path)
    else:
        shutil.copy2(no_subs, output_path)

    # Cleanup intermediate
    if os.path.exists(no_subs) and os.path.exists(output_path):
        try:
            os.remove(no_subs)
        except PermissionError:
            pass

    final_dur = _get_duration(output_path)
    print(f"  Final: {final_dur:.1f}s")

    return output_path


if __name__ == "__main__":
    ss = os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    vo = os.path.join(OUTPUT_FOLDER, "voiceover.mp3")
    if os.path.exists(ss) and os.path.exists(vo):
        composite_video(ss, vo)
    else:
        print("  Run slideshow_builder and tts_generator first")
