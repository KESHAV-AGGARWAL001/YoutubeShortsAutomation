"""
schedule_story_upload.py — Daily Story Series Uploader

Checks the series registry for any part scheduled for TODAY and uploads
it to Instagram using the shared upload flow.

Usage:
  python schedule_story_upload.py              # upload today's parts
  python schedule_story_upload.py --dry-run    # test without publishing
  python schedule_story_upload.py --status     # show what's scheduled
  python schedule_story_upload.py --force --series {id} --part 2  # force specific
  python schedule_story_upload.py --reset --series {id} --part 2  # re-upload failed

Automation:
  Windows Task Scheduler → run daily at 9:00 AM
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, date
from dotenv import load_dotenv

# Add parent directory so we can import shared module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.instagram_api import (
    verify_instagram_token,
    compress_video,
    upload_to_tmpfiles,
    create_container,
    wait_for_processing,
    publish_reel,
    cleanup_temp,
)

load_dotenv()

SERIES_DIR = "story_series"
REGISTRY   = os.path.join(SERIES_DIR, "series_registry.json")


# ── Registry & Meta ─────────────────────────────────────────────

def load_registry():
    if os.path.exists(REGISTRY):
        with open(REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"active_series": [], "completed_series": []}


def save_registry(registry):
    os.makedirs(SERIES_DIR, exist_ok=True)
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def load_meta(series_id):
    path = os.path.join(SERIES_DIR, series_id, "series_meta.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_meta(series_id, meta):
    path = os.path.join(SERIES_DIR, series_id, "series_meta.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def load_part_script(series_id, part_num):
    path = os.path.join(SERIES_DIR, series_id, f"part_{part_num}", "script.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_part_status(series_id, part_num):
    path = os.path.join(SERIES_DIR, series_id, f"part_{part_num}", "status.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_part_status(series_id, part_num, status_data):
    part_dir = os.path.join(SERIES_DIR, series_id, f"part_{part_num}")
    os.makedirs(part_dir, exist_ok=True)
    path = os.path.join(part_dir, "status.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)


def append_log(series_id, message):
    """Append to the upload log for this series."""
    log_path = os.path.join(SERIES_DIR, series_id, "upload_log.txt")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


# ── Find Today's Uploads ────────────────────────────────────────

def find_todays_uploads():
    """Find all parts scheduled for today across all active series."""
    registry = load_registry()
    today    = date.today().isoformat()
    uploads  = []

    for series_info in registry.get("active_series", []):
        series_id = series_info["series_id"]
        meta = load_meta(series_id)
        if not meta:
            continue

        schedule = meta.get("upload_schedule", {})
        parts_status = meta.get("parts_status", {})

        for part_key, scheduled_date in schedule.items():
            part_num = int(part_key.replace("part_", ""))

            if scheduled_date == today and parts_status.get(str(part_num)) == "pending":
                uploads.append({
                    "series_id":    series_id,
                    "series_title": meta["series_title"],
                    "part_num":     part_num,
                    "total_parts":  meta["total_parts"],
                    "category":     meta.get("category", "unknown"),
                })

    return uploads


# ── Upload Flow ─────────────────────────────────────────────────

def build_caption(part_script, series_meta, part_num, total_parts):
    """Build Instagram caption from part data."""
    caption_text = part_script.get("caption", "")
    cta          = part_script.get("cta", "")
    hashtags     = part_script.get("hashtags", "#nextlevelmind")
    series_title = series_meta.get("series_title", "")

    lines = []
    if caption_text:
        lines.append(caption_text)
    lines.append("")
    if cta:
        lines.append(cta)
    lines.append("")
    lines.append(f"📖 {series_title} — Part {part_num}/{total_parts}")
    lines.append("")
    lines.append(hashtags)

    return "\n".join(lines)


def upload_part(series_id, part_num, username, base_url, dry_run=False, skip_youtube=False, only_youtube=False):
    """Upload a single part to Instagram & YouTube. Returns dict with success status."""
    meta = load_meta(series_id)
    if not meta:
        print(f"  ❌ Series meta not found: {series_id}")
        return False

    total_parts = meta["total_parts"]
    series_title = meta["series_title"]

    print(f"\n  {'─' * 45}")
    print(f"  📖 {series_title}")
    print(f"  📲 Uploading Part {part_num}/{total_parts}")
    print(f"  {'─' * 45}")

    # Load script
    part_script = load_part_script(series_id, part_num)
    if not part_script:
        msg = f"Part {part_num}: script.json not found"
        print(f"  ❌ {msg}")
        append_log(series_id, f"FAILED — {msg}")
        return {"instagram_ok": False, "youtube_ok": False}

    # Check reel.mp4 exists
    reel_path = os.path.join(SERIES_DIR, series_id, f"part_{part_num}", "reel.mp4")
    if not os.path.exists(reel_path) or os.path.getsize(reel_path) < 10000:
        print(f"  ⚠️  reel.mp4 not found — attempting to render...")
        render_result = subprocess.run(
            [sys.executable, "render_story_reels.py",
             "--series", series_id, "--part", str(part_num)],
            capture_output=False
        )
        if render_result.returncode != 0 or not os.path.exists(reel_path):
            msg = f"Part {part_num}: render failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}

    reel_size = os.path.getsize(reel_path) / (1024 * 1024)
    print(f"  Video: reel.mp4 ({reel_size:.1f}MB)")
    print(f"  Title: {part_script.get('title', f'Part {part_num}')}")

    # Build caption
    caption = build_caption(part_script, meta, part_num, total_parts)
    cap_preview = caption[:100] + "..." if len(caption) > 100 else caption
    print(f"  Caption: {cap_preview}")

    if dry_run:
        print(f"\n  🧪 DRY RUN — skipping actual upload")
        append_log(series_id, f"DRY RUN — Part {part_num} ready but not uploaded")
        return {"instagram_ok": True, "youtube_ok": True}

    media_id = None
    video_url = None

    if not only_youtube:
        # Compress
        temp_folder = os.path.join(SERIES_DIR, series_id, f"part_{part_num}", "temp")
        os.makedirs(temp_folder, exist_ok=True)
        compressed_path = os.path.join(temp_folder, "compressed.mp4")

        print(f"\n  🎞️  Compressing video...")
        ret = subprocess.run([
            "ffmpeg", "-y", "-i", reel_path,
            "-c:v", "libx264", "-crf", "28", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            compressed_path
        ], capture_output=True)

        if ret.returncode != 0:
            msg = f"Part {part_num}: ffmpeg compression failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}

        # Upload to tmpfiles
        video_url = upload_to_tmpfiles(compressed_path)
        if not video_url:
            msg = f"Part {part_num}: tmpfiles upload failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}

        # Create container
        container_id = create_container(caption, video_url, base_url)
        if not container_id:
            msg = f"Part {part_num}: container creation failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}

        # Wait for processing
        print(f"  Waiting for Instagram to process...")
        ready = wait_for_processing(container_id, base_url)
        if not ready:
            msg = f"Part {part_num}: processing failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}

        # Publish
        media_id = publish_reel(container_id, base_url)
        if not media_id:
            msg = f"Part {part_num}: publish failed"
            print(f"  ❌ {msg}")
            append_log(series_id, f"FAILED — {msg}")
            return {"instagram_ok": False, "youtube_ok": False}
    else:
        print(f"\n  ⏭️  Skipping Instagram Upload (--only-youtube flag enabled)")

    # ── YouTube Shorts Upload (simultaneous) ─────────────────────────
    from shared.youtube_api import upload_part_to_youtube

    print(f"\n  {'─' * 45}")
    print(f"  🎬 Uploading to YouTube Shorts...")

    yt_result = upload_part_to_youtube(
        video_path  = reel_path,      # original reel.mp4 — NOT the compressed temp
        part_script = part_script,
        series_meta = meta,
        part_num    = part_num,
        total_parts = total_parts,
        dry_run     = dry_run or skip_youtube,
    )

    if yt_result and yt_result.get("video_id"):
        yt_video_id  = yt_result["video_id"]
        yt_playlist  = yt_result.get("playlist_id", "")
        yt_comment   = yt_result.get("comment_id", "")
        yt_url       = yt_result.get("url", "")
        append_log(series_id, f"YOUTUBE — Part {part_num} | {yt_url}")
        print(f"  🎉 YouTube Short live: {yt_url}")
    else:
        yt_video_id = yt_playlist = yt_comment = yt_url = None
        if not (yt_result and yt_result.get("dry_run")):
            append_log(series_id, f"YOUTUBE FAILED — Part {part_num}")
            print(f"  ⚠️  YouTube upload failed — Instagram succeeded")

    # Update status
    now = datetime.now().isoformat(timespec="seconds")
    default_status = load_part_status(series_id, part_num) or {}

    save_part_status(series_id, part_num, {
        "part_number":          part_num,
        "status":               "uploaded",
        "uploaded_at":          now,
        # Instagram fields (keep existing if skipping IG)
        "instagram_media_id":   media_id if media_id else default_status.get("instagram_media_id", ""),
        "scheduled_date":       meta["upload_schedule"].get(f"part_{part_num}", ""),
        "tmpfiles_url":         video_url if video_url else default_status.get("tmpfiles_url", ""),
        # YouTube fields
        "youtube_video_id":     yt_video_id,
        "youtube_playlist_id":  yt_playlist,
        "youtube_comment_id":   yt_comment,
        "youtube_url":          yt_url,
    })

    # Update series meta
    meta["parts_status"][str(part_num)] = "uploaded"

    # Check if all parts uploaded
    all_done = all(s == "uploaded" for s in meta["parts_status"].values())

    if all_done:
        meta["status"] = "completed"
    elif part_num < total_parts:
        next_date = meta["upload_schedule"].get(f"part_{part_num + 1}", "")
        meta["next_upload"] = {"part": part_num + 1, "date": next_date}

    save_meta(series_id, meta)

    # Update registry
    registry = load_registry()
    if all_done:
        # Move to completed
        registry["active_series"] = [
            s for s in registry["active_series"] if s["series_id"] != series_id
        ]
        registry["completed_series"].append({
            "series_id":    series_id,
            "series_title": meta["series_title"],
            "category":     meta.get("category", ""),
            "total_parts":  total_parts,
            "completed_at": now,
        })
    else:
        # Update next upload info
        for s in registry["active_series"]:
            if s["series_id"] == series_id:
                s["next_upload_part"] = part_num + 1
                next_date = meta["upload_schedule"].get(f"part_{part_num + 1}", "")
                s["next_upload_date"] = next_date
                break

    save_registry(registry)

    if not only_youtube:
        append_log(series_id, f"UPLOADED — Part {part_num}/{total_parts} | Media ID: {media_id}")
        print(f"  🎉 Part {part_num} published! Media ID: {media_id}")
        print(f"     https://www.instagram.com/{username}/")
        ig_success = True
    else:
        ig_success = True  # Treat as technically successful since we intentionally skipped it

    return {"instagram_ok": ig_success, "youtube_ok": yt_video_id is not None or bool(yt_result and yt_result.get("dry_run"))}


# ── Show Status ─────────────────────────────────────────────────

def show_status():
    """Show what's scheduled for today."""
    today   = date.today().isoformat()
    uploads = find_todays_uploads()

    print(f"\n  📅 Today's uploads ({today}):")
    print(f"  {'─' * 45}")

    if not uploads:
        print(f"  No parts scheduled for today.")
        registry = load_registry()
        active = registry.get("active_series", [])
        if active:
            print(f"\n  Active series:")
            for s in active:
                print(f"    {s['series_title']}")
                print(f"    Next: Part {s.get('next_upload_part', '?')} on {s.get('next_upload_date', '?')}")
        return

    for u in uploads:
        print(f"  📖 {u['series_title']}")
        print(f"     Part {u['part_num']}/{u['total_parts']} ({u['category']})")
        print(f"     Series: {u['series_id']}")
        print()

    print(f"  Total: {len(uploads)} part(s) ready to upload")
    print(f"  Run: python schedule_story_upload.py")


# ── CLI ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload today's scheduled story parts")
    parser.add_argument("--dry-run", action="store_true", help="Test without publishing")
    parser.add_argument("--status",  action="store_true", help="Show today's schedule")
    parser.add_argument("--force",   action="store_true", help="Force upload (ignore schedule)")
    parser.add_argument("--reset",   action="store_true", help="Reset a failed part to pending")
    parser.add_argument("--no-youtube", action="store_true", help="Skip YouTube upload, Instagram only")
    parser.add_argument("--only-youtube", action="store_true", help="Skip Instagram upload, YouTube only")
    parser.add_argument("--series",  type=str,            help="Specific series ID")
    parser.add_argument("--part",    type=int,            help="Specific part number")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  📅 Story Series Uploader — NextLevelMind")
    print(f"  Date: {date.today().isoformat()}")
    print("=" * 55)

    # Status mode
    if args.status:
        show_status()
        return

    # Reset mode
    if args.reset and args.series and args.part:
        meta = load_meta(args.series)
        if meta:
            meta["parts_status"][str(args.part)] = "pending"
            save_meta(args.series, meta)

            save_part_status(args.series, args.part, {
                "part_number":        args.part,
                "status":             "pending",
                "scheduled_date":     meta["upload_schedule"].get(f"part_{args.part}", ""),
                "uploaded_at":        None,
                "instagram_media_id": None,
                "tmpfiles_url":       None,
            })
            append_log(args.series, f"RESET — Part {args.part} marked as pending")
            print(f"\n  ✅ Part {args.part} of {args.series} reset to pending")
        else:
            print(f"\n  ❌ Series not found: {args.series}")
        return

    # Verify Instagram token once
    username, base_url = verify_instagram_token()
    if not username:
        print("\n  ❌ Instagram token verification failed!")
        print("     Run: python test_instagram_upload.py --exchange-token")
        sys.exit(1)
    print(f"  Authenticated as @{username}")

    if args.force and args.series and args.part:
        print(f"\n  ⚡ Force uploading: {args.series} Part {args.part}")
        result = upload_part(args.series, args.part, username, base_url, dry_run=args.dry_run, skip_youtube=args.no_youtube, only_youtube=args.only_youtube)
        if not result.get("instagram_ok", False) and not args.only_youtube:
            sys.exit(1)
        return

    # Find today's uploads
    uploads = find_todays_uploads()

    if not uploads:
        print(f"\n  📭 No parts scheduled for today ({date.today().isoformat()})")
        show_status()
        return

    print(f"\n  Found {len(uploads)} part(s) to upload today")

    if args.dry_run:
        print(f"  Mode: DRY RUN")

    # Upload each part
    results = {}
    for u in uploads:
        result = upload_part(
            u["series_id"], u["part_num"],
            username, base_url,
            dry_run=args.dry_run,
            skip_youtube=args.no_youtube,
            only_youtube=args.only_youtube
        )
        results[f"{u['series_title']} Part {u['part_num']}"] = result

    # Summary
    print(f"\n{'=' * 55}")
    print(f"  Upload Summary — {date.today().isoformat()}")
    print(f"{'=' * 55}")
    for label, result in results.items():
        ig_ok = result.get("instagram_ok", False)
        yt_ok = result.get("youtube_ok", False)
        print(f"  {label}:")
        print(f"    Instagram: {'✅ Published' if ig_ok else '❌ Failed'}")
        print(f"    YouTube:   {'✅ Published' if yt_ok else '❌ Failed / Skipped'}")

    total    = len(results)
    success_ig = sum(1 for v in results.values() if v.get("instagram_ok"))
    print(f"\n  {success_ig}/{total} Instagram uploads successful")

    if success_ig < total:
        print(f"  ⚠️  Some uploads failed — check logs above")
        print(f"  Re-run: python schedule_story_upload.py --reset --series <id> --part <n>")

    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
