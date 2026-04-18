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
_script_label = "Retention-optimized script (V2)" if _script_version == "v2" else "Finding topic + writing script (Gemini)"

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
    Schedule both videos for TODAY.
    Preferred times: 9:00 AM EST (14:00 UTC) and 4:00 PM EST (21:00 UTC).
    If a preferred time has already passed, schedule 15 min from now instead
    (YouTube requires at least 5 min in the future for scheduled uploads).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    buffer = datetime.timedelta(minutes=15)

    # Preferred times today
    m_utc = now.replace(hour=14, minute=0, second=0, microsecond=0)  # 9:00 AM EST
    e_utc = now.replace(hour=21, minute=0, second=0, microsecond=0)  # 4:00 PM EST

    # If preferred time already passed → use 15 min from now
    if m_utc <= now:
        m_utc  = now + buffer
        m_label = f"~{(now + buffer).strftime('%I:%M %p')} UTC (9AM EST passed, publishing now)"
    else:
        m_label = "9:00 AM EST (USA morning)"

    if e_utc <= now:
        e_utc  = now + buffer + datetime.timedelta(minutes=5)  # slight offset from Video 1
        e_label = f"~{(now + buffer + datetime.timedelta(minutes=5)).strftime('%I:%M %p')} UTC (4PM EST passed, publishing now)"
    else:
        e_label = "4:00 PM EST (USA evening)"

    return (
        m_utc.strftime(fmt), m_label,
        e_utc.strftime(fmt), e_label,
    )


def run_pipeline(video_num, schedule_utc, schedule_label):
    print(f"\n{'#'*50}")
    print(f"  VIDEO {video_num}/2")
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
    print("  2 YouTube videos per day")
    print("="*50)

    os.makedirs("output",  exist_ok=True)
    os.makedirs("archive", exist_ok=True)
    os.makedirs("reels",   exist_ok=True)

    m_utc, m_label, e_utc, e_label = get_schedules()

    print(f"\n  Schedule:")
    print(f"  YouTube 1   → {m_label}")
    print(f"  YouTube 2   → {e_label}")

    run_pipeline(1, m_utc, m_label)
    run_pipeline(2, e_utc, e_label)

    print("\n" + "="*50)
    print("  ALL DONE!")
    print(f"  YouTube 1 → live at {m_label}")
    print(f"  YouTube 2 → live at {e_label}")
    print(f"  Studio: https://studio.youtube.com")
    print("="*50)


if __name__ == "__main__":
    main()