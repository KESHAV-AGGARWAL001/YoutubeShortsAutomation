"""
test_main.py — Full Test Pipeline

Runs EVERYTHING including:
  - Script writing (Gemini)
  - Voiceover (Edge TTS)
  - Footage selection
  - Video assembly (FFmpeg)
  - Thumbnail generation
  - Reel creation (9:16 vertical)
  - Email delivery (Gmail)

Skips ONLY:
  - YouTube upload (07_upload.py)

Saves all outputs to temp/ folder for review.
Check your Gmail after running — Reel will be in your inbox!
"""

import subprocess
import sys
import os
import shutil
import datetime

TEST_STEPS = [
    ("02_write_script.py", "Finding topic + writing script (Gemini)",        False),
    ("03_voiceover.py",    "Generating voiceover (Edge TTS)",                 False),
    ("04_get_footage.py",  "Selecting footage (2 random categories)",         False),
    ("05_make_video.py",   "Assembling video (FFmpeg)",                       False),
    ("06_thumbnail.py",    "Generating thumbnail (Pillow)",                   False),
    # 07_upload.py intentionally skipped — test mode
    ("08_make_reel.py",    "Creating Instagram Reel (9:16 vertical)",         True),
    ("09_send_email.py",   "Emailing Reel package to Gmail",                  True),
]

TEMP_FOLDER = "temp"


def run_step(script, label, step_num, total, optional=False):
    print(f"\n{'='*50}")
    print(f"  STEP {step_num}/{total}: {label}")
    if script == "07_upload.py":
        print(f"  SKIPPED — test mode (no YouTube upload)")
        return True
    print(f"{'='*50}")

    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        capture_output=False
    )

    if result.returncode != 0:
        if optional:
            print(f"\n  WARNING: {script} failed — continuing anyway")
            return False
        print(f"\n  ERROR in {script}. Stopping.")
        sys.exit(1)

    return True


def save_to_temp(video_num, timestamp):
    """Copy all outputs to temp/ folder for review"""
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    saved = []

    files_to_save = {
        "output/final_video.mp4":  f"test_video_{video_num}_{timestamp}.mp4",
        "output/thumbnail.jpg":    f"test_thumb_{video_num}_{timestamp}.jpg",
        "output/latest_script.txt":f"test_script_{video_num}_{timestamp}.txt",
        "output/seo_data.json":    f"test_seo_{video_num}_{timestamp}.json",
        "output/subtitles.srt":    f"test_subtitles_{video_num}_{timestamp}.srt",
    }

    for src, dest_name in files_to_save.items():
        if os.path.exists(src):
            dest = f"{TEMP_FOLDER}/{dest_name}"
            shutil.copy2(src, dest)
            size_mb = os.path.getsize(dest) // (1024 * 1024)
            label   = dest_name.split("_")[1]
            print(f"  Saved {label:10s}: {dest_name} ({size_mb} MB)")
            saved.append(dest)

    # Save latest reel files
    reels_dir = "reels"
    if os.path.exists(reels_dir):
        for f in sorted(os.listdir(reels_dir)):
            src = f"{reels_dir}/{f}"
            # Only copy files created in this run (recent)
            if os.path.getmtime(src) > (datetime.datetime.now().timestamp() - 600):
                dest = f"{TEMP_FOLDER}/test_reel_{video_num}_{f}"
                shutil.copy2(src, dest)
                size_mb = os.path.getsize(dest) // (1024 * 1024)
                print(f"  Saved reel      : {os.path.basename(dest)} ({size_mb} MB)")
                saved.append(dest)

    return saved


def clean_output():
    """Clean output between video 1 and video 2"""
    folders = [
        "output/voiceovers",
        "output/clips",
        "output/sections",
    ]
    files = [
        "output/final_video.mp4",
        "output/thumbnail.jpg",
        "output/latest_script.txt",
        "output/seo_data.json",
        "output/quotes_used.json",
        "output/video_theme.json",
        "output/stock_concat.txt",
        "output/section_timings.json",
        "output/subtitles.srt",
        "output/clip_list.json",
        "output/audio_list.txt",
        "output/full_voiceover.mp3",
        "output/final_audio.mp3",
        "output/video_no_music.mp4",
        "output/video_clean.mp4",
        "output/video_for_reel.mp4",
    ]
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    for f in files:
        if os.path.exists(f):
            os.remove(f)

    os.makedirs("output", exist_ok=True)

    # Preserve YouTube token
    if os.path.exists("output/token.json"):
        pass  # already preserved — not in files list

    print("  Output cleaned for next video\n")


def run_test_pipeline(video_num):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'#'*50}")
    print(f"  TEST VIDEO {video_num}/2")
    print(f"  YouTube upload: SKIPPED")
    print(f"  Reel + Email:   INCLUDED")
    print(f"{'#'*50}")

    os.environ["VIDEO_NUMBER"] = str(video_num)

    # Set a test schedule time (tomorrow noon IST) for display purposes
    tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    if video_num == 1:
        sched = tomorrow.replace(hour=6,  minute=30, second=0, microsecond=0)
        label = "12:00 PM IST (test)"
    else:
        sched = tomorrow.replace(hour=12, minute=30, second=0, microsecond=0)
        label = "6:00 PM IST (test)"

    os.environ["PUBLISH_TIME_UTC"] = sched.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    total = len(TEST_STEPS)
    for i, (script, lbl, optional) in enumerate(TEST_STEPS, 1):
        run_step(script, lbl, i, total, optional=optional)

    # Save to temp
    print(f"\n  Saving test outputs to {TEMP_FOLDER}/...")
    saved = save_to_temp(video_num, timestamp)
    print(f"  {len(saved)} files saved")

    print(f"\n  Video {video_num} test complete!")
    print(f"  Would have gone live at: {label}")

    clean_output()


def print_summary():
    """Print a clear summary of what was created"""
    print("\n" + "="*50)
    print("  TEST COMPLETE — REVIEW YOUR OUTPUTS")
    print("="*50)

    # Temp folder files
    if os.path.exists(TEMP_FOLDER):
        print(f"\n  📁 C:\\YouTubeBot\\{TEMP_FOLDER}\\ contents:")
        for f in sorted(os.listdir(TEMP_FOLDER)):
            full  = f"{TEMP_FOLDER}/{f}"
            size  = os.path.getsize(full) // (1024 * 1024)
            ext   = f.split(".")[-1].upper()
            print(f"    [{ext:4s}] {f}  ({size} MB)")

    # Reels folder
    if os.path.exists("reels"):
        reel_vids = [f for f in os.listdir("reels") if f.endswith(".mp4")]
        reel_txts = [f for f in os.listdir("reels") if f.endswith(".txt")]
        if reel_vids:
            print(f"\n  📱 C:\\YouTubeBot\\reels\\ contents:")
            for f in sorted(os.listdir("reels")):
                full = f"reels/{f}"
                size = os.path.getsize(full) // (1024 * 1024)
                print(f"    {f}  ({size} MB)")

    print(f"\n  ✅ CHECK THESE NOW:")
    print(f"  1. Open temp/ folder → watch both .mp4 videos")
    print(f"  2. Check both .jpg thumbnails")
    print(f"  3. Open Gmail → 2 emails from yourself")
    print(f"     → Download the Reel .mp4 from email")
    print(f"     → Copy caption + hashtags from email body")
    print(f"  4. Open reels/ folder → check vertical .mp4 files")
    print(f"\n  ✅ HAPPY WITH EVERYTHING?")
    print(f"  Run: python main.py")
    print(f"  That uploads to YouTube + sends reels for real!")
    print("="*50)


def main():
    print("\n" + "="*50)
    print("  NextLevelMind — TEST MODE")
    print("  No YouTube upload · Full Reel + Email test")
    print("="*50)

    os.makedirs("output", exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    os.makedirs("reels", exist_ok=True)

    print(f"\n  What this test does:")
    print(f"  ✅ Writes script with Gemini")
    print(f"  ✅ Generates voiceover with Edge TTS")
    print(f"  ✅ Assembles full YouTube-style video")
    print(f"  ✅ Creates 9:16 vertical Instagram Reel")
    print(f"  ✅ Emails Reel + caption to your Gmail")
    print(f"  ⏭️  Skips YouTube upload (test mode)")
    print(f"\n  After running — check Gmail on your phone!")

    # Test Video 1
    run_test_pipeline(1)

    # Test Video 2
    run_test_pipeline(2)

    # Summary
    print_summary()


if __name__ == "__main__":
    main()