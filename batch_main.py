"""
batch_main.py — Weekly Batch Content Production

Generates an entire week's content in ONE run:
  - 14 YouTube Shorts (2 per day x 7 days)
  - 7 Long-form videos (1 per day x 7 days)
  - 7 Community posts (1 per day, emailed)

All videos uploaded with staggered schedules across the week:
  Each day: Long-form 6 AM EST | Short #1 9 AM EST | Short #2 4 PM EST

Usage:
  python batch_main.py
"""

import subprocess
import sys
import os
import shutil
import datetime
from dotenv import load_dotenv

load_dotenv()

# Pick script version from .env (v1 or v2)
_sv = os.getenv("SCRIPT_VERSION", "v1").strip().lower()
_write_short = "02_write_script_v2.py" if _sv == "v2" else "02_write_script.py"

SHORTS_STEPS = [
    (_write_short,         "Writing script"),
    ("03_voiceover.py",    "Generating voiceover"),
    ("04_get_footage.py",  "Selecting footage"),
    ("05_make_video.py",   "Assembling video"),
    ("07_upload_v2.py",    "Uploading + Playlist"),
    ("community_post.py",  "Community Post + Email"),
]

LONG_STEPS = [
    ("long_02_write_script.py", "Writing long-form script"),
    ("03_voiceover.py",         "Generating voiceover"),
    ("04_get_footage.py",       "Setting up background"),
    ("long_05_make_video.py",   "Assembling 16:9 video"),
    ("long_06_thumbnail.py",    "Generating AI thumbnail"),
    ("long_07_upload.py",       "Uploading to YouTube"),
    ("community_post.py",       "Community Post + Email"),
]

OPTIONAL_SCRIPTS = {
    "07_upload_v2.py", "community_post.py",
    "long_07_upload.py", "long_06_thumbnail.py",
}


def run_step(script, label, step_num, total):
    optional = script in OPTIONAL_SCRIPTS
    print(f"  [{step_num}/{total}] {label}...")
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        capture_output=False
    )
    if result.returncode != 0:
        if optional:
            print(f"  WARNING: {script} failed — continuing")
            return True  # non-fatal
        print(f"  ERROR in {script}.")
        return False
    return True


def cleanup_output():
    saved = {}
    for keep in ("token.json", "playlist_cache.json"):
        path = f"output/{keep}"
        if os.path.exists(path):
            with open(path, "r") as f:
                saved[keep] = f.read()

    if os.path.exists("output"):
        for _ in range(5):
            try:
                shutil.rmtree("output")
                break
            except PermissionError:
                import time; time.sleep(1)

    os.makedirs("output", exist_ok=True)

    for keep, data in saved.items():
        with open(f"output/{keep}", "w") as f:
            f.write(data)


def archive_video(label):
    os.makedirs("archive", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for src, suffix in [
        ("output/final_video.mp4", ".mp4"),
        ("output/community_post.jpg", "_community.jpg"),
        ("output/community_post_text.txt", "_community.txt"),
    ]:
        if os.path.exists(src):
            shutil.copy2(src, f"archive/{label}_{ts}{suffix}")


def calculate_weekly_schedule():
    now = datetime.datetime.now(datetime.timezone.utc)
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    schedule = []

    for day in range(7):
        base = tomorrow + datetime.timedelta(days=day)
        schedule.append({
            "day": day + 1,
            "date": base.strftime("%a %b %d"),
            "long_utc":   base.replace(hour=11, minute=0).strftime(fmt),  # 6 AM EST
            "short1_utc": base.replace(hour=14, minute=0).strftime(fmt),  # 9 AM EST
            "short2_utc": base.replace(hour=21, minute=0).strftime(fmt),  # 4 PM EST
        })

    return schedule


def run_pipeline(steps, schedule_utc, label, video_num="1"):
    os.environ["PUBLISH_TIME_UTC"] = schedule_utc
    os.environ["VIDEO_NUMBER"] = str(video_num)

    total = len(steps)
    for i, (script, step_label) in enumerate(steps, 1):
        if not run_step(script, step_label, i, total):
            print(f"  {label} FAILED — skipping to next")
            return False

    archive_video(label)
    cleanup_output()
    return True


def main():
    print("\n" + "=" * 60)
    print("  NextLevelMind — WEEKLY BATCH PRODUCTION")
    print("  14 Shorts + 7 Long-form + 7 Community Posts")
    print("=" * 60)

    os.makedirs("output", exist_ok=True)
    os.makedirs("archive", exist_ok=True)

    schedule = calculate_weekly_schedule()

    # Print schedule
    print("\n  SCHEDULE (next 7 days):")
    print("  " + "-" * 50)
    for d in schedule:
        print(f"  Day {d['day']} ({d['date']}): Long 6AM | Short1 9AM | Short2 4PM EST")
    print("  " + "-" * 50)

    ok = {"short": 0, "long": 0}
    fail = {"short": 0, "long": 0}

    for d in schedule:
        day = d["day"]
        print(f"\n{'#'*60}")
        print(f"  DAY {day}/7 — {d['date']}")
        print(f"{'#'*60}")

        # Long-form (6 AM EST)
        print(f"\n  --- Long-form (6 AM EST) ---")
        if run_pipeline(LONG_STEPS, d["long_utc"], f"day{day}_long"):
            ok["long"] += 1
        else:
            fail["long"] += 1

        # Short #1 (9 AM EST)
        print(f"\n  --- Short #1 (9 AM EST) ---")
        if run_pipeline(SHORTS_STEPS, d["short1_utc"], f"day{day}_short1", "1"):
            ok["short"] += 1
        else:
            fail["short"] += 1

        # Short #2 (4 PM EST)
        print(f"\n  --- Short #2 (4 PM EST) ---")
        if run_pipeline(SHORTS_STEPS, d["short2_utc"], f"day{day}_short2", "2"):
            ok["short"] += 1
        else:
            fail["short"] += 1

        print(f"\n  Day {day} done — Long: {'OK' if ok['long'] >= day else 'FAIL'} | "
              f"Shorts: {ok['short']}/{day * 2}")

    # Final report
    total_ok = ok["short"] + ok["long"]
    total_fail = fail["short"] + fail["long"]

    print("\n" + "=" * 60)
    print("  WEEKLY BATCH COMPLETE!")
    print("=" * 60)
    print(f"  Shorts  : {ok['short']}/14 uploaded")
    print(f"  Long    : {ok['long']}/7 uploaded")
    print(f"  Total   : {total_ok}/{total_ok + total_fail} videos")
    if total_fail:
        print(f"  Failed  : {total_fail}")
    print(f"\n  All videos scheduled across next 7 days")
    print(f"  Archive : archive/")
    print(f"  Studio  : https://studio.youtube.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
