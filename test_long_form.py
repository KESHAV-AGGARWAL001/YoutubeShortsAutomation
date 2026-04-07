"""
test_long_form.py — Test the long-form video pipeline end-to-end (no upload)

Runs every step except YouTube upload so you can verify:
  - Script generation (Gemini)
  - Voiceover (Edge TTS)
  - Video assembly (FFmpeg — 16:9, centered text)
  - Thumbnail generation
  - SEO data + timestamps

Usage:
  python test_long_form.py
"""

import subprocess
import sys
import os
import json
import time

STEPS = [
    ("scripts/long_02_write_script.py", "Script Generation (Gemini)"),
    ("scripts/03_voiceover.py",         "Voiceover (Edge TTS)"),
    ("scripts/04_get_footage.py",       "Background Setup"),
    ("scripts/long_05_make_video.py",   "Video Assembly (16:9)"),
    ("scripts/long_06_thumbnail.py",    "Thumbnail Generation"),
]


def run_step(script, label, step_num, total):
    print(f"\n{'='*60}")
    print(f"  TEST STEP {step_num}/{total}: {label}")
    print(f"  Script: {script}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        capture_output=False
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n  FAILED: {script} (exit code {result.returncode})")
        print(f"  Time: {elapsed:.1f}s")
        return False

    print(f"\n  PASSED ({elapsed:.1f}s)")
    return True


def check_outputs():
    """Verify all expected output files exist and print details."""
    print(f"\n{'='*60}")
    print(f"  OUTPUT VERIFICATION")
    print(f"{'='*60}")

    checks = [
        ("output/seo_data.json",     "SEO Data"),
        ("output/latest_script.txt", "Full Script"),
        ("output/final_video.mp4",   "Final Video"),
        ("output/subtitles.srt",     "Subtitles (SRT)"),
        ("output/thumbnail.jpg",     "Thumbnail"),
        ("output/full_voiceover.mp3","Merged Voiceover"),
    ]

    all_good = True
    for filepath, label in checks:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 1024 * 1024:
                size_str = f"{size // (1024 * 1024)} MB"
            elif size > 1024:
                size_str = f"{size // 1024} KB"
            else:
                size_str = f"{size} bytes"
            print(f"  [OK]   {label:25s} → {size_str:>10s}  ({filepath})")
        else:
            print(f"  [MISS] {label:25s} → NOT FOUND  ({filepath})")
            all_good = False

    # Check voiceover sections
    vo_dir = "output/voiceovers"
    if os.path.exists(vo_dir):
        vo_files = sorted([f for f in os.listdir(vo_dir) if f.endswith(".mp3")])
        print(f"\n  Voiceover sections: {len(vo_files)}")
        for f in vo_files:
            size_kb = os.path.getsize(os.path.join(vo_dir, f)) // 1024
            print(f"    {f} ({size_kb} KB)")

    # Check section text files
    sec_dir = "output/sections"
    if os.path.exists(sec_dir):
        sec_files = sorted([f for f in os.listdir(sec_dir) if f.endswith(".txt")])
        print(f"\n  Script sections: {len(sec_files)}")
        for f in sec_files:
            with open(os.path.join(sec_dir, f), "r", encoding="utf-8") as fh:
                text = fh.read().strip()
            words = len(text.split())
            print(f"    {f} ({words} words)")

    # Print SEO data
    if os.path.exists("output/seo_data.json"):
        with open("output/seo_data.json", "r", encoding="utf-8") as f:
            seo = json.load(f)
        print(f"\n  SEO Details:")
        print(f"    Title      : {seo.get('youtube_title', 'N/A')}")
        print(f"    Tags       : {len(seo.get('tags', []))} tags")
        print(f"    Category   : {seo.get('category_id', 'N/A')}")
        print(f"    Long-form  : {seo.get('is_long_form', False)}")
        print(f"    Chapters   : {len(seo.get('chapter_titles', []))}")

        # Print chapter titles
        chapters = seo.get("chapter_titles", [])
        if chapters:
            print(f"\n  Chapter Titles:")
            for i, ch in enumerate(chapters):
                print(f"    {i+1}. {ch}")

        # Check description length
        desc = seo.get("description", "")
        print(f"\n  Description  : {len(desc)} chars (YouTube limit: 5000)")
        if "TIMESTAMPS_PLACEHOLDER" in desc:
            print(f"    [WARN] TIMESTAMPS_PLACEHOLDER not replaced yet (normal — replaced at upload time)")
        if "amzn.to" in desc:
            print(f"    [OK] Affiliate links present")
        else:
            print(f"    [MISS] No affiliate links found")

    # Print full script word count
    if os.path.exists("output/latest_script.txt"):
        with open("output/latest_script.txt", "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        word_count = len(script_text.split())
        est_minutes = word_count / 160
        print(f"\n  Script Stats:")
        print(f"    Words      : {word_count}")
        print(f"    Est. Time  : {est_minutes:.1f} minutes (at 160 wpm)")
        if word_count < 900:
            print(f"    [WARN] Script might be too short for 7-8 min video")
        elif word_count > 1600:
            print(f"    [WARN] Script might be too long (>10 min)")
        else:
            print(f"    [OK] Word count in ideal range (900-1600)")

    # Check video duration
    if os.path.exists("output/final_video.mp4"):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                "output/final_video.mp4"
            ], capture_output=True, text=True, timeout=15)
            duration = float(result.stdout.strip())
            print(f"\n  Video Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
            if duration < 300:
                print(f"    [WARN] Video is under 5 minutes — may not qualify for mid-roll ads")
            elif duration > 600:
                print(f"    [WARN] Video is over 10 minutes — might lose retention")
            else:
                print(f"    [OK] Duration in ideal range (5-10 min)")
        except Exception:
            pass

    # Check video resolution
    if os.path.exists("output/final_video.mp4"):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                "output/final_video.mp4"
            ], capture_output=True, text=True, timeout=15)
            dims = result.stdout.strip()
            print(f"  Resolution   : {dims} (expected: 1920,1080)")
            if dims == "1920,1080":
                print(f"    [OK] Correct 16:9 horizontal format")
            else:
                print(f"    [WARN] Unexpected resolution — should be 1920x1080")
        except Exception:
            pass

    return all_good


def main():
    print("\n" + "=" * 60)
    print("  LONG-FORM VIDEO PIPELINE — TEST RUN")
    print("  (No upload — just generate and verify)")
    print("=" * 60)

    os.makedirs("output", exist_ok=True)

    # Run all steps except upload
    total = len(STEPS)
    results = []
    total_start = time.time()

    for i, (script, label) in enumerate(STEPS, 1):
        success = run_step(script, label, i, total)
        results.append((label, success))
        if not success and script != "scripts/long_06_thumbnail.py":
            print(f"\n  Pipeline stopped — {label} failed.")
            print(f"  Fix the error above and re-run this test.")
            break

    total_elapsed = time.time() - total_start

    # Verify outputs
    outputs_ok = check_outputs()

    # Summary
    print(f"\n{'='*60}")
    print(f"  TEST RESULTS")
    print(f"{'='*60}")
    for label, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {label}")
    print(f"\n  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"  Outputs: {'ALL PRESENT' if outputs_ok else 'SOME MISSING'}")

    if all(s for _, s in results) and outputs_ok:
        print(f"\n  ALL TESTS PASSED!")
        print(f"  Your long-form video is ready at: output/final_video.mp4")
        print(f"  Thumbnail: output/thumbnail.jpg")
        print(f"\n  To upload: python scripts/long_07_upload.py")
    else:
        print(f"\n  SOME TESTS FAILED — check errors above")

    print("=" * 60)


if __name__ == "__main__":
    main()
