"""
test_reel.py — Quick Reel-Only Test

Tests ONLY the Instagram Reel creation + direct upload to Instagram,
using whatever video is already in output/.

What it does:
  1. Checks for output/video_for_reel.mp4 (clean, no YouTube subs)
  2. Falls back to output/final_video.mp4 if clean version missing
  3. Creates a vertical 1080x1920 reel with Instagram-optimized subtitles
  4. Uploads the reel directly to Instagram via Graph API
  5. Saves everything to temp/ for review

Usage:
  python test_reel.py

Prerequisites:
  - Run 05_make_video.py first (or the full pipeline) so a source video exists
  - .env must have GEMINI_API_KEY, INSTAGRAM_TOKEN, INSTAGRAM_ID
"""
import subprocess
import sys
import os
import datetime
import shutil

TEMP_FOLDER = "temp"

def run_script(script, label, optional=False):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        capture_output=False
    )
    if result.returncode != 0:
        if optional:
            print(f"  WARNING: {script} failed — continuing")
            return False
        print(f"  ERROR in {script}")
        return False
    return True


def main():
    print("\n" + "=" * 50)
    print("  REEL TEST — Instagram Reel Only")
    print("  No script/voiceover/video generation")
    print("=" * 50)

    # Check for source video
    if os.path.exists("output/video_for_reel.mp4"):
        source = "output/video_for_reel.mp4"
        print(f"\n  ✅ Found CLEAN source (no YouTube subs)")
    elif os.path.exists("output/final_video.mp4"):
        source = "output/final_video.mp4"
        print(f"\n  ⚠️  Using final_video.mp4 (HAS YouTube subtitles!)")
        print(f"  For best results, run 05_make_video.py to get video_for_reel.mp4")
    else:
        print(f"\n  ❌ No source video found!")
        print(f"  Run at least steps 02-05 first:")
        print(f"    python scripts/02_write_script.py")
        print(f"    python scripts/03_voiceover.py")
        print(f"    python scripts/04_get_footage.py")
        print(f"    python scripts/05_make_video.py")
        return

    size_mb = os.path.getsize(source) // (1024 * 1024)
    print(f"  Source: {source} ({size_mb} MB)")

    # Check for other required files
    if os.path.exists("output/subtitles.srt"):
        print(f"  SRT: output/subtitles.srt ✓")
    else:
        print(f"  SRT: not found — reel will have no subtitles")

    if os.path.exists("output/seo_data.json"):
        print(f"  SEO: output/seo_data.json ✓")
    else:
        print(f"  SEO: not found — using defaults")

    os.makedirs("reels", exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # Set environment for reel scripts
    os.environ["VIDEO_NUMBER"] = "1"

    # Run reel creation
    print("\n" + "-" * 50)
    success_reel = run_script("08_make_reel.py", "Creating Instagram Reel")

    if not success_reel:
        print("\n  Reel creation failed!")
        return

    # Run Instagram upload
    print("\n" + "-" * 50)
    run_script("09_upload_instagram.py", "Uploading Reel to Instagram", optional=True)

    # Copy reel files to temp for review
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n  Copying reel files to {TEMP_FOLDER}/...")

    for f in sorted(os.listdir("reels")):
        src = f"reels/{f}"
        # Only recent files (last 10 minutes)
        if os.path.getmtime(src) > (datetime.datetime.now().timestamp() - 600):
            dest = f"{TEMP_FOLDER}/test_{f}"
            shutil.copy2(src, dest)
            size = os.path.getsize(dest) // (1024 * 1024)
            print(f"    {f} ({size} MB)")

    # Summary
    print("\n" + "=" * 50)
    print("  REEL TEST COMPLETE")
    print("=" * 50)
    print(f"\n  📂 Check these locations:")
    print(f"     reels/   → vertical MP4 + cover + upload card")
    print(f"     temp/    → copies for review")
    print(f"\n  📲 Check your Instagram profile for the uploaded reel")
    print(f"\n  🔍 What to verify:")
    print(f"     1. Open the vertical .mp4 — check subtitles are readable")
    print(f"     2. Subtitles should be CENTERED (not at bottom)")
    print(f"     3. No double/overlapping text from YouTube version")
    print(f"     4. @nextlevelmind_km watermark visible at top")
    print(f"     5. Cover image looks good")
    print(f"\n  Happy? Run: python main.py (for full production)")
    print("=" * 50)


if __name__ == "__main__":
    main()
