"""
Kids Poems YouTube Channel — Video Pipeline

Fully automated: generates poem, creates images, voiceover,
slideshow, subtitles, and uploads to YouTube.

Usage:
  python main.py              # Generate and upload 3 videos
  python main.py --no-upload  # Generate only, skip upload

Pipeline:
  1. Gemini generates original poem + visual descriptions + SEO
  2. Gemini generates colorful illustrations per verse
  3. Edge TTS creates warm child-friendly voiceover
  4. FFmpeg builds Ken Burns slideshow from images
  5. FFmpeg burns colorful subtitles + mixes music
  6. YouTube API uploads with Made for Kids = True
"""

import os
import sys
import time
import json
import shutil
import datetime
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_FOLDER, POEM_CATEGORIES, CHANNEL_NAME, VEO_ENABLED
from poem_generator import generate_poem
from image_generator import generate_all_images
from tts_generator import generate_voiceover
from slideshow_builder import build_slideshow
from video_compositor import composite_video
from youtube_uploader import upload_video

if VEO_ENABLED:
    from video_clip_generator import generate_all_clips
    from clip_concatenator import concatenate_clips, image_to_video_segment
    from image_generator import generate_fallback_images


def cleanup_output():
    """Clean output folder between videos, preserving auth tokens."""
    saved = {}
    for keep in ("token_kp.json",):
        path = os.path.join(os.path.dirname(OUTPUT_FOLDER), keep)
        if os.path.exists(path):
            with open(path, "rb") as f:
                saved[keep] = f.read()

    if os.path.exists(OUTPUT_FOLDER):
        for attempt in range(5):
            try:
                shutil.rmtree(OUTPUT_FOLDER)
                break
            except PermissionError:
                time.sleep(1)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for keep, data in saved.items():
        path = os.path.join(os.path.dirname(OUTPUT_FOLDER), keep)
        with open(path, "wb") as f:
            f.write(data)


def archive_video(label):
    """Copy final video to archive folder."""
    archive_dir = os.path.join(os.path.dirname(OUTPUT_FOLDER), "archive")
    os.makedirs(archive_dir, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final = os.path.join(OUTPUT_FOLDER, "final_video.mp4")
    if os.path.exists(final):
        dest = os.path.join(archive_dir, f"{label}_{ts}.mp4")
        shutil.copy2(final, dest)
        print(f"  Archived: {dest}")


def get_schedules():
    """
    Schedule 3 videos for today.
    9 AM EST, 4 PM EST, 8 PM EST (peak times for parent + kid viewing).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    buffer = datetime.timedelta(minutes=15)

    slots = [
        (now.replace(hour=14, minute=0, second=0, microsecond=0),
         "9:00 AM EST (morning cartoons)"),
        (now.replace(hour=21, minute=0, second=0, microsecond=0),
         "4:00 PM EST (after school)"),
        ((now + datetime.timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0),
         "8:00 PM EST (bedtime)"),
    ]

    result = []
    for i, (slot_utc, label) in enumerate(slots):
        if slot_utc <= now:
            slot_utc = now + buffer + datetime.timedelta(minutes=5 * i)
            label = f"~{slot_utc.strftime('%I:%M %p')} UTC (scheduling now)"
        result.append((slot_utc.strftime(fmt), label))

    return result


def run_single_pipeline(category=None, schedule_utc=None, video_num=1,
                        total_videos=3, skip_upload=False):
    """Run the full pipeline for one video."""
    start = time.time()
    category = category or random.choice(POEM_CATEGORIES)

    print(f"\n{'#' * 55}")
    print(f"  VIDEO {video_num}/{total_videos} — {category}")
    print(f"{'#' * 55}")

    # Step 1: Generate poem
    print("\n[Step 1/6] Generating poem...")
    poem_data = generate_poem(category)
    print(f"  Title: {poem_data['youtube_title']}")
    for line in poem_data["poem_lines"]:
        print(f"    {line}")
    print("  Done")

    # Save poem data
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(os.path.join(OUTPUT_FOLDER, "poem_data.json"), "w", encoding="utf-8") as f:
        json.dump(poem_data, f, indent=2, ensure_ascii=False)

    slideshow_path = os.path.join(OUTPUT_FOLDER, "slideshow.mp4")

    if VEO_ENABLED:
        # Veo path: voiceover first (need timings for clip durations)
        print("\n[Step 2/6] Generating voiceover...")
        vo_path, vo_duration, timings = generate_voiceover(poem_data["poem_lines"])
        print("  Done")

        print("\n[Step 3/6] Generating animated clips (Veo 3.1)...")
        clip_paths, failed_indices = generate_all_clips(poem_data, timings)

        if len(failed_indices) == len(poem_data.get("visual_descriptions", [])):
            # Total failure — fall back to legacy image + slideshow pipeline
            print("  All clips failed — falling back to static images...")
            print("\n[Step 3b/6] Generating images (fallback)...")
            images = generate_all_images(poem_data)
            if not images:
                print("  ERROR: No images generated — skipping video")
                return False
            print("\n[Step 4/6] Building slideshow (fallback)...")
            build_slideshow(images, slideshow_path, target_duration=vo_duration, timings=timings)
        else:
            # Handle partial failures with image fallback
            if failed_indices:
                print(f"\n  Generating fallback images for {len(failed_indices)} failed clips...")
                fb_images = generate_fallback_images(poem_data, failed_indices)
                for idx in failed_indices:
                    if idx in fb_images:
                        fb_video = os.path.join(OUTPUT_FOLDER, "clips", f"fb_{idx:02d}.mp4")
                        dur = timings[idx]["end"] - timings[idx]["start"]
                        if idx + 1 < len(timings):
                            dur += timings[idx + 1]["start"] - timings[idx]["end"]
                        dur = max(2.0, dur)
                        seg = image_to_video_segment(fb_images[idx], fb_video, dur)
                        if seg:
                            clip_paths[idx] = seg

            # Filter out any remaining None entries
            valid_clips = [p for p in clip_paths if p]
            valid_timings = [t for i, t in enumerate(timings) if clip_paths[i]]

            if not valid_clips:
                print("  ERROR: No clips available — skipping video")
                return False

            print("\n[Step 4/6] Concatenating animated clips...")
            concatenate_clips(valid_clips, slideshow_path, timings=valid_timings)

        print("  Done")
    else:
        # Legacy path: static images + Ken Burns slideshow
        print("\n[Step 2/6] Generating images...")
        images = generate_all_images(poem_data)
        if not images:
            print("  ERROR: No images generated — skipping video")
            return False
        print("  Done")

        print("\n[Step 3/6] Generating voiceover...")
        vo_path, vo_duration, timings = generate_voiceover(poem_data["poem_lines"])
        print("  Done")

        print("\n[Step 4/6] Building slideshow...")
        build_slideshow(images, slideshow_path, target_duration=vo_duration, timings=timings)
        print("  Done")

    # Step 5: Composite final video (slideshow + voice + music + subtitles)
    print("\n[Step 5/6] Compositing final video...")
    final_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")
    composite_video(
        slideshow_path, vo_path, final_path,
        category=category, timings=timings
    )
    print("  Done")

    # Step 6: Upload to YouTube
    if skip_upload:
        print("\n[Step 6/6] Upload SKIPPED (--no-upload)")
        video_id = "skipped"
    else:
        print("\n[Step 6/6] Uploading to YouTube...")
        full_desc = poem_data["description"]
        video_id = upload_video(
            final_path,
            poem_data["youtube_title"],
            full_desc,
            poem_data.get("tags", []),
            schedule_utc=schedule_utc,
        )
        print("  Done")

    # Archive + cleanup
    archive_video(f"{category}_{video_num}")
    cleanup_output()

    elapsed = time.time() - start
    print(f"\n  Video {video_num} complete in {elapsed:.0f}s")
    return True


def main():
    skip_upload = "--no-upload" in sys.argv

    print("\n" + "=" * 55)
    print(f"  {CHANNEL_NAME} — Kids Poems Pipeline")
    print(f"  3 YouTube Shorts per day")
    print("=" * 55)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    schedules = get_schedules()
    categories = random.sample(
        POEM_CATEGORIES, min(3, len(POEM_CATEGORIES))
    )

    print(f"\n  Schedule ({len(schedules)} videos):")
    for i, (utc, label) in enumerate(schedules):
        print(f"  Video {i + 1} [{categories[i]}] → {label}")

    ok = 0
    fail = 0

    for i, (utc, label) in enumerate(schedules):
        schedule = None if skip_upload else utc
        if run_single_pipeline(
            category=categories[i],
            schedule_utc=schedule,
            video_num=i + 1,
            total_videos=len(schedules),
            skip_upload=skip_upload,
        ):
            ok += 1
        else:
            fail += 1

    print("\n" + "=" * 55)
    print(f"  ALL DONE!")
    print(f"  Success: {ok}/{ok + fail}")
    if fail:
        print(f"  Failed: {fail}")
    print(f"  Studio: https://studio.youtube.com")
    print("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
