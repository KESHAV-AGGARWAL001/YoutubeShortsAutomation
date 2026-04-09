"""
long_form_main.py — Long-Form Video Pipeline Runner

Runs 1 long-form video per day (7-8 minutes).
Schedule: 6:00 AM EST (11:00 UTC) — before Shorts go live.

Pipeline:
  1. long_02_write_script.py — Read 8-10 pages, generate structured script
  2. 03_voiceover.py         — Same TTS script (handles any number of sections)
  3. 04_get_footage.py        — Same (black background)
  4. long_05_make_video.py   — 16:9 assembly with centered subs
  5. long_06_thumbnail.py    — Generate thumbnail
  6. long_07_upload.py       — Upload as regular video
"""

import subprocess
import sys
import os
import shutil
import datetime


STEPS = [
    ("long_02_write_script.py", "Generating long-form script (Gemini)"),
    ("03_voiceover.py",         "Generating voiceover (Edge TTS)"),
    ("04_get_footage.py",       "Setting up background"),
    ("long_05_make_video.py",   "Assembling 16:9 video (FFmpeg)"),
    ("long_06_thumbnail.py",    "Generating thumbnail"),
    ("long_07_upload.py",       "Uploading to YouTube"),
]


def run_step(script, label, step_num, total, optional=False):
    print(f"\n{'='*50}")
    print(f"  STEP {step_num}/{total}: {label}")
    print(f"{'='*50}")
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        capture_output=False
    )
    if result.returncode != 0:
        if optional:
            print(f"\n  WARNING: {script} failed — continuing")
            return False
        print(f"\n  ERROR in {script}. Stopping pipeline.")
        sys.exit(1)
    return True


def cleanup_output():
    print("\n  Cleaning up output folder...")
    archive_dir = "archive"
    os.makedirs(archive_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if os.path.exists("output/final_video.mp4"):
        shutil.copy2("output/final_video.mp4", f"{archive_dir}/long_video_{timestamp}.mp4")
        print(f"  Video backed up: archive/long_video_{timestamp}.mp4")

    saved_token = None
    if os.path.exists("output/token.json"):
        with open("output/token.json", "r") as f:
            saved_token = f.read()

    saved_playlist_cache = None
    if os.path.exists("output/playlist_cache.json"):
        with open("output/playlist_cache.json", "r") as f:
            saved_playlist_cache = f.read()

    if os.path.exists("output"):
        for attempt in range(5):
            try:
                shutil.rmtree("output")
                print("  Output folder deleted")
                break
            except PermissionError:
                import time; time.sleep(1)

    os.makedirs("output", exist_ok=True)

    if saved_token:
        with open("output/token.json", "w") as f:
            f.write(saved_token)
        print("  YouTube auth token preserved")

    if saved_playlist_cache:
        with open("output/playlist_cache.json", "w") as f:
            f.write(saved_playlist_cache)
        print("  Playlist cache preserved")


def get_schedule():
    """
    Schedule long-form video for 6:00 AM EST (11:00 UTC).
    If that time already passed today, publish 15 min from now.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    buffer = datetime.timedelta(minutes=15)

    # 6:00 AM EST = 11:00 UTC
    target = now.replace(hour=11, minute=0, second=0, microsecond=0)

    if target <= now:
        target = now + buffer
        label = f"~{(now + buffer).strftime('%I:%M %p')} UTC (6AM EST passed, publishing soon)"
    else:
        label = "6:00 AM EST (before Shorts go live)"

    return target.strftime(fmt), label


def main():
    print("\n" + "=" * 50)
    print("  NextLevelMind — Long-Form Content Bot")
    print("  1 long video per day (7-8 minutes)")
    print("=" * 50)

    os.makedirs("output",  exist_ok=True)
    os.makedirs("archive", exist_ok=True)

    schedule_utc, schedule_label = get_schedule()

    print(f"\n  Schedule: {schedule_label}")
    print(f"  UTC     : {schedule_utc}")

    os.environ["PUBLISH_TIME_UTC"] = schedule_utc

    total = len(STEPS)
    upload_success = True
    for i, (script, label) in enumerate(STEPS, 1):
        optional = script in ("long_07_upload.py", "long_06_thumbnail.py")
        result = run_step(script, label, i, total, optional=optional)
        if script == "long_07_upload.py" and not result:
            upload_success = False

    print(f"\n  LONG-FORM VIDEO COMPLETE!")
    print(f"  YouTube: {schedule_label}")

    if upload_success:
        cleanup_output()
    else:
        # Don't delete artifacts — user may want to retry upload manually
        print("\n  Upload failed — keeping output/ intact for manual retry")
        if os.path.exists("output/final_video.mp4"):
            archive_dir = "archive"
            os.makedirs(archive_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2("output/final_video.mp4", f"{archive_dir}/long_video_{timestamp}.mp4")
            print(f"  Video backed up: archive/long_video_{timestamp}.mp4")
        print("  To retry: python scripts/long_07_upload.py")

    print("\n" + "=" * 50)
    print("  ALL DONE!")
    print(f"  Long-form video → live at {schedule_label}")
    print(f"  Studio: https://studio.youtube.com")
    print("=" * 50)


if __name__ == "__main__":
    main()
