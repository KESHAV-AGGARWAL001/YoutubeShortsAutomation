import subprocess
import sys
import os
import shutil
import datetime
from dotenv import load_dotenv

load_dotenv()

# Pick script version based on SCRIPT_VERSION env var
_script_version = os.getenv("SCRIPT_VERSION", "v1").strip().lower()
_write_script = "02_write_script_v2.py" if _script_version == "v2" else "02_write_script.py"
_script_label = "Retention-optimized script (V2)" if _script_version == "v2" else "Finding topic + writing script (Groq)"

STEPS = [
    (_write_script,         _script_label),
    ("03_voiceover.py",     "Generating voiceover (Edge TTS)"),
    ("04_get_footage.py",   "Selecting footage (2 random categories)"),
    ("05_make_video.py",    "Assembling video (FFmpeg)"),
    ("07_upload.py",        "Uploading to YouTube Shorts"),
    ("community_post.py",   "Generating YouTube Community Post"),
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
        shutil.copy2("output/final_video.mp4", f"{archive_dir}/video_{timestamp}.mp4")
        print(f"  Video backed up: archive/video_{timestamp}.mp4")

    if os.path.exists("output/community_post.jpg"):
        shutil.copy2("output/community_post.jpg", f"{archive_dir}/community_post_{timestamp}.jpg")
        print(f"  Community post image backed up: archive/community_post_{timestamp}.jpg")

    if os.path.exists("output/community_post_text.txt"):
        shutil.copy2("output/community_post_text.txt", f"{archive_dir}/community_post_{timestamp}.txt")
        print(f"  Community post text backed up: archive/community_post_{timestamp}.txt")

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


def get_schedules():
    """
    Schedule 3 videos for TODAY.
    Preferred times: 9:00 AM EST (14:00 UTC), 4:00 PM EST (21:00 UTC),
    and 8:00 PM EST (01:00 UTC next day) — peak mobile scroll time.
    If a preferred time has already passed, schedule 15 min from now instead.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    buffer = datetime.timedelta(minutes=15)

    # Preferred times today (UTC)
    m_utc = now.replace(hour=14, minute=0, second=0, microsecond=0)  # 9:00 AM EST
    e_utc = now.replace(hour=21, minute=0, second=0, microsecond=0)  # 4:00 PM EST
    n_utc = (now + datetime.timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0)  # 8:00 PM EST

    slots = [
        (m_utc, "9:00 AM EST (USA morning)"),
        (e_utc, "4:00 PM EST (USA evening)"),
        (n_utc, "8:00 PM EST (peak scroll)"),
    ]

    result = []
    for i, (slot_utc, slot_label) in enumerate(slots):
        if slot_utc <= now:
            offset = buffer + datetime.timedelta(minutes=5 * i)
            slot_utc = now + offset
            slot_label = f"~{slot_utc.strftime('%I:%M %p')} UTC ({slot_label} passed, publishing now)"
        result.append((slot_utc.strftime(fmt), slot_label))

    return result


def run_pipeline(video_num, total_videos, schedule_utc, schedule_label):
    print(f"\n{'#'*50}")
    print(f"  VIDEO {video_num}/{total_videos}")
    print(f"  YouTube goes live: {schedule_label}")
    print(f"{'#'*50}")

    os.environ["PUBLISH_TIME_UTC"] = schedule_utc
    os.environ["VIDEO_NUMBER"]     = str(video_num)

    total = len(STEPS)
    upload_success = True
    for i, (script, label) in enumerate(STEPS, 1):
        # Upload step is optional — don't crash pipeline if it fails
        optional = script in ("07_upload.py", "community_post.py")
        result = run_step(script, label, i, total, optional=optional)
        if script == "07_upload.py" and not result:
            upload_success = False

    print(f"\n  VIDEO {video_num} COMPLETE!")
    print(f"  YouTube: {schedule_label}")

    if upload_success:
        cleanup_output()
    else:
        print("\n  Upload failed — keeping output/ intact for manual retry")
        print("  To retry: python scripts/07_upload.py")


def main():
    print("\n" + "="*50)
    print("  NextLevelMind — Daily Content Bot")
    print("  3 YouTube Shorts per day (YPP growth mode)")
    print("="*50)

    os.makedirs("output",  exist_ok=True)
    os.makedirs("archive", exist_ok=True)
    os.makedirs("reels",   exist_ok=True)

    schedules = get_schedules()
    total = len(schedules)

    print(f"\n  Schedule ({total} videos):")
    for i, (utc, label) in enumerate(schedules, 1):
        print(f"  YouTube {i}   → {label}")

    for i, (utc, label) in enumerate(schedules, 1):
        run_pipeline(i, total, utc, label)

    print("\n" + "="*50)
    print("  ALL DONE!")
    for i, (utc, label) in enumerate(schedules, 1):
        print(f"  YouTube {i} → live at {label}")
    print(f"  Studio: https://studio.youtube.com")
    print("="*50)


if __name__ == "__main__":
    main()