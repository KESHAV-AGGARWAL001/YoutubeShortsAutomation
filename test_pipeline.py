"""
test_pipeline.py — Full Pipeline Test (NO upload)

Tests every script in the pipeline including all new additions:
  ✅ 02_write_script.py  — Gemini AI script + viral titles + trending tags + A/B context
  ✅ 03_voiceover.py     — Edge TTS voiceover
  ✅ 04_get_footage.py   — Footage selection + subtitle timings
  ✅ 05_make_video.py    — Video assembly + SRT generation
  ✅ 06_thumbnail.py     — Dark cinematic thumbnail (new design)
  ✅ get_trending_tags.py — Trending tag fetcher (unit test)
  ✅ analytics_tracker.py — Upload logger + pattern detection (dry run)
  ✅ SEO validation       — Verifies title format, tag count, category_id, description structure

Outputs saved to: test_output/
Upload step (07_upload.py) is intentionally skipped.
"""

import subprocess
import sys
import os
import json
import shutil
import datetime

# ── Config ────────────────────────────────────────────────────────────

PIPELINE_STEPS = [
    ("02_write_script.py", "Gemini AI script + viral title + trending tags"),
    ("03_voiceover.py",    "Edge TTS voiceover"),
    ("04_get_footage.py",  "Footage selection + subtitle timings"),
    ("05_make_video.py",   "Video assembly + SRT subtitle file"),
    ("06_thumbnail.py",    "Dark cinematic thumbnail (new design)"),
]

TEMP_FOLDER = "test_output"


# ── Pipeline Runner ───────────────────────────────────────────────────

def run_step(script, label, step_num, total):
    print(f"\n{'='*55}")
    print(f"  STEP {step_num}/{total}: {label}")
    print(f"{'='*55}")
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"],
        capture_output=False
    )
    if result.returncode != 0:
        print(f"\n  ERROR in {script}. Stopping pipeline.")
        sys.exit(1)


# ── SEO Validator ─────────────────────────────────────────────────────

def validate_seo_output():
    """
    Validate that 02_write_script.py produced correct SEO metadata.
    Checks all new Phase 1 requirements.
    """
    seo_file = "output/seo_data.json"
    if not os.path.exists(seo_file):
        print("  [FAIL] seo_data.json not found")
        return False

    with open(seo_file, "r", encoding="utf-8") as f:
        seo = json.load(f)

    passed = True
    results = []

    # Title checks
    title = seo.get("youtube_title", "")
    if "#Shorts" in title or "#shorts" in title:
        results.append(("PASS", f"Title contains #Shorts: \"{title}\""))
    else:
        results.append(("FAIL", f"Title missing #Shorts: \"{title}\""))
        passed = False

    if len(title) <= 100:
        results.append(("PASS", f"Title length OK: {len(title)} chars"))
    else:
        results.append(("FAIL", f"Title too long: {len(title)} chars (max 100)"))
        passed = False

    # Check book name not in title (basic check for common book-related words)
    if ".pdf" not in title.lower():
        results.append(("PASS", "Title does not contain .pdf extension"))
    else:
        results.append(("FAIL", "Title contains .pdf — book name leaked into title"))
        passed = False

    # Tags checks
    tags = seo.get("tags", [])
    if len(tags) >= 25:
        results.append(("PASS", f"Tag count: {len(tags)} tags (target: 30+)"))
    else:
        results.append(("WARN", f"Tag count low: {len(tags)} tags (target: 30+)"))

    # Category ID check
    category_id = seo.get("category_id")
    if category_id in ("22", "27"):
        cat_name = "People & Blogs" if category_id == "22" else "Education"
        results.append(("PASS", f"category_id: {category_id} ({cat_name})"))
    else:
        results.append(("FAIL", f"category_id missing or wrong: {category_id}"))
        passed = False

    # Angle type check
    angle = seo.get("angle_type", "")
    if angle:
        results.append(("PASS", f"angle_type: {angle}"))
    else:
        results.append(("WARN", "angle_type not set"))

    # Description first-line check
    desc = seo.get("description", "")
    first_line = desc.split("\n")[0] if desc else ""
    if len(first_line) > 30:
        results.append(("PASS", f"Description line 1 ({len(first_line)} chars): \"{first_line[:60]}...\""))
    else:
        results.append(("WARN", f"Description line 1 is short: \"{first_line}\""))

    # Hashtag block check
    if "#Shorts" in desc and "#YouTubeShorts" in desc:
        results.append(("PASS", "Description contains #Shorts and #YouTubeShorts hashtag block"))
    else:
        results.append(("FAIL", "Description missing #Shorts or #YouTubeShorts hashtag block"))
        passed = False

    # Print results
    print(f"\n  {'─'*50}")
    print(f"  SEO VALIDATION REPORT")
    print(f"  {'─'*50}")
    for status, msg in results:
        icon = "✅" if status == "PASS" else ("⚠️ " if status == "WARN" else "❌")
        print(f"  {icon} [{status}] {msg}")
    print(f"  {'─'*50}")
    print(f"  Overall: {'PASSED' if passed else 'FAILED'}")

    return passed


# ── Trending Tags Unit Test ───────────────────────────────────────────

def test_trending_tags():
    """Unit test for get_trending_tags.py — tests both pytrends and fallback."""
    print(f"\n{'='*55}")
    print(f"  UNIT TEST: get_trending_tags.py")
    print(f"{'='*55}")

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
    try:
        from get_trending_tags import get_trending_tags
    except ImportError as e:
        print(f"  [FAIL] Could not import get_trending_tags: {e}")
        return False

    categories = ["discipline_habits", "success_mindset", "general"]
    all_passed = True

    for cat in categories:
        tags = get_trending_tags(category=cat)
        if tags and len(tags) >= 3:
            print(f"  ✅ [{cat}] returned {len(tags)} tags: {tags[:3]}...")
        else:
            print(f"  ❌ [{cat}] returned too few tags: {tags}")
            all_passed = False

    return all_passed


# ── Analytics Tracker Dry Run ─────────────────────────────────────────

def test_analytics_tracker():
    """
    Dry-run test for analytics_tracker.py.
    Logs a fake video entry and verifies pattern detection works.
    Does NOT call YouTube Analytics API.
    """
    print(f"\n{'='*55}")
    print(f"  UNIT TEST: analytics_tracker.py (dry run)")
    print(f"{'='*55}")

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
    try:
        from analytics_tracker import log_upload, get_top_patterns, _detect_pattern
    except ImportError as e:
        print(f"  [FAIL] Could not import analytics_tracker: {e}")
        return False

    all_passed = True

    # Test pattern detection
    test_cases = [
        ("Stop Doing This If You Want to Win #Shorts",       "stop_doing"),
        ("Nobody Told Me This Would Change Everything #Shorts", "nobody_told_me"),
        ("The Brutal Truth About Why You're Losing #Shorts",  "brutal_truth"),
        ("99% of People Get This Completely Wrong #Shorts",   "99_percent"),
        ("I Wish Someone Had Told Me This Sooner #Shorts",    "i_wish_i_knew"),
    ]

    print("\n  Pattern Detection Tests:")
    for title, expected in test_cases:
        detected = _detect_pattern(title)
        if detected == expected:
            print(f"  ✅ \"{title[:45]}...\" → [{detected}]")
        else:
            print(f"  ❌ \"{title[:45]}...\" → [{detected}] (expected [{expected}])")
            all_passed = False

    # Test log_upload with fake video_id
    print("\n  Log Upload Test (fake video):")
    fake_id = "TEST_VIDEO_DRY_RUN"
    entry = log_upload(
        video_id    = fake_id,
        title       = "Stop Doing This If You Want to Win #Shorts",
        angle_type  = "direct advice",
        category_id = "27",
    )
    if entry and entry.get("video_id") == fake_id:
        print(f"  ✅ log_upload() created entry for {fake_id}")
    else:
        print(f"  ❌ log_upload() failed")
        all_passed = False

    # Test get_top_patterns (may return empty — that's fine for dry run)
    patterns = get_top_patterns()
    print(f"  ✅ get_top_patterns() returned {len(patterns)} patterns (empty is OK — no real data yet)")

    return all_passed


# ── Save Test Outputs ─────────────────────────────────────────────────

def save_test_outputs(video_num):
    """Save all generated files to test_output/ for manual inspection."""
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []

    files_to_save = {
        "output/final_video.mp4":    f"video_{video_num}_{timestamp}.mp4",
        "output/thumbnail.jpg":      f"thumbnail_{video_num}_{timestamp}.jpg",
        "output/subtitles.srt":      f"subtitles_{video_num}_{timestamp}.srt",
        "output/seo_data.json":      f"seo_data_{video_num}_{timestamp}.json",
        "output/latest_script.txt":  f"script_{video_num}_{timestamp}.txt",
    }

    for src, dst_name in files_to_save.items():
        if os.path.exists(src):
            dst = os.path.join(TEMP_FOLDER, dst_name)
            shutil.copy2(src, dst)
            saved.append(dst_name)

    print(f"\n  Saved to {TEMP_FOLDER}/:")
    for name in saved:
        print(f"    ✅ {name}")

    return saved


def clean_output():
    """Clean working output/ directory between runs."""
    print("\n  Cleaning output/ for next run...")
    if os.path.exists("output"):
        for attempt in range(5):
            try:
                shutil.rmtree("output")
                break
            except PermissionError:
                import time; time.sleep(1)
    os.makedirs("output", exist_ok=True)

    # Preserve token and cache between runs
    for keep_file in ["output/token.json", "output/playlist_cache.json"]:
        pass  # Already deleted with rmtree — main.py preserves these, test mode doesn't need to


# ── Per-Video Test Run ────────────────────────────────────────────────

def run_test_video(video_num):
    print(f"\n{'#'*55}")
    print(f"  TEST VIDEO {video_num}/2")
    print(f"{'#'*55}")

    os.environ["VIDEO_NUMBER"] = str(video_num)

    total = len(PIPELINE_STEPS)
    for i, (script, label) in enumerate(PIPELINE_STEPS, 1):
        run_step(script, label, i, total)

    # Validate SEO output from step 1
    print(f"\n  Running SEO validation...")
    validate_seo_output()

    # Save everything for review
    save_test_outputs(video_num)
    clean_output()


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*55)
    print("  NextLevelMind — FULL PIPELINE TEST")
    print("  Runs all steps | Skips upload | Validates SEO")
    print("="*55)
    print(f"\n  Output folder : {TEMP_FOLDER}/")
    print(f"  Upload        : SKIPPED (test mode)")
    print(f"  Thumbnail     : ENABLED (new dark cinematic design)")
    print(f"  SRT Captions  : ENABLED (saved to test_output/)")
    print(f"  Trending Tags : ENABLED (Google Trends + evergreen fallback)")
    print(f"  A/B Analytics : DRY RUN (no YouTube API calls)")

    clean_output()

    # ── Unit tests (no API calls) ──────────────────────────────────
    trending_ok  = test_trending_tags()
    analytics_ok = test_analytics_tracker()

    # ── Full pipeline (2 videos) ───────────────────────────────────
    run_test_video(1)
    run_test_video(2)

    # ── Final summary ──────────────────────────────────────────────
    print("\n" + "="*55)
    print("  TEST COMPLETE!")
    print("="*55)
    print(f"\n  Unit Tests:")
    print(f"    Trending Tags  : {'✅ PASSED' if trending_ok  else '❌ FAILED'}")
    print(f"    Analytics A/B  : {'✅ PASSED' if analytics_ok else '❌ FAILED'}")
    print(f"\n  Generated files saved to: {TEMP_FOLDER}/")
    print(f"    - 2x final_video.mp4    → watch your Shorts")
    print(f"    - 2x thumbnail.jpg      → check CTR design")
    print(f"    - 2x subtitles.srt      → verify caption timing")
    print(f"    - 2x seo_data.json      → inspect titles/tags/description")
    print(f"    - 2x script .txt        → read the AI-generated scripts")
    print(f"\n  To run the real pipeline (with upload):")
    print(f"    python main.py")
    print("="*55)


if __name__ == "__main__":
    main()
