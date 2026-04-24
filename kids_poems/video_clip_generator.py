"""
video_clip_generator.py — Veo 3.1 Animated Clip Generator for Kids Poems

Generates one short animated cartoon clip per poem verse using
Google's Veo 3.1 video generation API. Falls back to Veo Lite
if the primary model fails.
"""

import os
import sys
import time
import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    GEMINI_API_KEY, VEO_MODEL, VEO_LITE_MODEL, VEO_USE_LITE,
    VEO_TIMEOUT, VEO_MAX_WORKERS,
    OUTPUT_FOLDER,
)

from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)


def pick_veo_duration(needed_seconds):
    """Map voiceover line duration to nearest Veo-supported duration (4, 6, or 8)."""
    if needed_seconds <= 4.0:
        return 4
    if needed_seconds <= 6.0:
        return 6
    return 8


def generate_video_clip(visual_description, output_path, duration_seconds=4, index=0):
    """
    Generate a single animated clip from a visual description using Veo 3.1.
    Returns True on success, False on failure.
    """
    prompt = (
        f"Create a gentle animated children's cartoon scene: {visual_description}. "
        f"Style: cute 2D animation, bright vivid colors, simple shapes, "
        f"child-friendly, happy mood, smooth slow gentle motion, "
        f"no text or words, no scary elements, "
        f"high quality digital animation, colorful background, "
        f"safe for toddlers."
    )

    models_to_try = [VEO_MODEL]
    if VEO_USE_LITE:
        models_to_try.append(VEO_LITE_MODEL)

    for model in models_to_try:
        for attempt in range(3):
            try:
                operation = client.models.generate_videos(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(
                        number_of_videos=1,
                        duration_seconds=duration_seconds,
                        aspect_ratio="9:16",
                    ),
                )

                result = operation.result(timeout=VEO_TIMEOUT)

                if result and result.generated_videos:
                    video = result.generated_videos[0]
                    if video.video and video.video.uri:
                        video_data = client.files.download(file=video.video)
                        with open(output_path, "wb") as f:
                            f.write(video_data)
                    elif video.video and video.video.video_bytes:
                        vid_data = video.video.video_bytes
                        if isinstance(vid_data, str):
                            vid_data = base64.b64decode(vid_data)
                        with open(output_path, "wb") as f:
                            f.write(vid_data)
                    else:
                        print(f"    Clip {index + 1}: No video data in response")
                        continue

                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        size_kb = os.path.getsize(output_path) / 1024
                        print(f"    Clip {index + 1}: {size_kb:.0f}KB ({duration_seconds}s) — {model}")
                        return True

                print(f"    Clip {index + 1}: Empty response from {model}")

            except Exception as e:
                wait = [5, 15, 30][attempt]
                print(f"    Clip {index + 1}: Attempt {attempt + 1}/3 failed ({model}) — {e}")
                if attempt < 2:
                    time.sleep(wait)

        if model == VEO_MODEL and VEO_USE_LITE:
            print(f"    Clip {index + 1}: Falling back to Veo Lite...")

    return False


def generate_all_clips(poem_data, timings):
    """
    Generate animated clips for all poem verses in parallel.
    Returns (clip_paths, failed_indices).
    clip_paths[i] is the path string or None if failed.
    """
    visuals = poem_data.get("visual_descriptions", [])
    clips_dir = os.path.join(OUTPUT_FOLDER, "clips")
    os.makedirs(clips_dir, exist_ok=True)

    clip_paths = [None] * len(visuals)
    failed_indices = []

    durations = []
    for i, t in enumerate(timings):
        needed = t["end"] - t["start"]
        if i + 1 < len(timings):
            gap = timings[i + 1]["start"] - t["end"]
            needed += gap * 0.5
        durations.append(needed)

    print(f"  Generating {len(visuals)} animated clips (Veo 3.1)...")

    def _gen(i, desc, dur):
        clip_path = os.path.join(clips_dir, f"clip_{i:02d}.mp4")
        veo_dur = pick_veo_duration(dur)
        ok = generate_video_clip(desc, clip_path, veo_dur, i)
        return i, clip_path if ok else None

    workers = min(VEO_MAX_WORKERS, len(visuals))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_gen, i, desc, durations[i] if i < len(durations) else 4.0): i
            for i, desc in enumerate(visuals)
        }
        for future in as_completed(futures):
            idx, path = future.result()
            if path:
                clip_paths[idx] = path
            else:
                failed_indices.append(idx)

    failed_indices.sort()
    ok_count = len(visuals) - len(failed_indices)
    print(f"  Clips generated: {ok_count}/{len(visuals)}")
    if failed_indices:
        print(f"  Failed verses: {failed_indices}")

    return clip_paths, failed_indices


def main():
    print("=" * 50)
    print("  Kids Poem Animated Clip Generator (Veo 3.1)")
    print("=" * 50)

    poem_file = os.path.join(OUTPUT_FOLDER, "poem_data.json")
    timings_file = os.path.join(OUTPUT_FOLDER, "line_timings.json")

    if not os.path.exists(poem_file):
        print("  ERROR: Run poem_generator.py first")
        return
    if not os.path.exists(timings_file):
        print("  ERROR: Run tts_generator.py first")
        return

    with open(poem_file, "r", encoding="utf-8") as f:
        poem_data = json.load(f)
    with open(timings_file, "r", encoding="utf-8") as f:
        timings = json.load(f)

    print(f"\n  Poem: {poem_data.get('poem_title', 'Unknown')}")
    clip_paths, failed = generate_all_clips(poem_data, timings)

    ok = sum(1 for p in clip_paths if p)
    print(f"\n  Generated {ok} clips, {len(failed)} failed")
    print("=" * 50)


if __name__ == "__main__":
    main()
