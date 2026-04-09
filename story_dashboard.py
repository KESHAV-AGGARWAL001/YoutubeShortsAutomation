"""
story_dashboard.py — Story Series Status Dashboard

Shows all active and completed series with upload progress,
schedule info, and what's due today/tomorrow.

Usage:
  python story_dashboard.py
"""

import os
import json
from datetime import date, timedelta


SERIES_DIR = "story_series"
REGISTRY   = os.path.join(SERIES_DIR, "series_registry.json")


def load_registry():
    if os.path.exists(REGISTRY):
        with open(REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"active_series": [], "completed_series": []}


def load_meta(series_id):
    path = os.path.join(SERIES_DIR, series_id, "series_meta.json")
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


def has_reel(series_id, part_num):
    path = os.path.join(SERIES_DIR, series_id, f"part_{part_num}", "reel.mp4")
    return os.path.exists(path) and os.path.getsize(path) > 10000


def format_date(date_str):
    """Convert 2026-03-30 to Mar 30."""
    try:
        d = date.fromisoformat(date_str)
        return d.strftime("%b %d")
    except (ValueError, TypeError):
        return date_str or "?"


def main():
    today     = date.today()
    tomorrow  = today + timedelta(days=1)
    today_str = today.isoformat()
    tmrw_str  = tomorrow.isoformat()

    registry = load_registry()
    active   = registry.get("active_series", [])
    completed = registry.get("completed_series", [])

    # ── Header ──
    W = 58
    print()
    print("╔" + "═" * W + "╗")
    print("║" + "  📺 NextLevelMind — Story Series Dashboard".center(W) + "║")
    print("╠" + "═" * W + "╣")

    # ── Active Series ──
    today_count = 0

    if active:
        print("║" + f"  ACTIVE SERIES ({len(active)})".ljust(W) + "║")
        print("╠" + "═" * W + "╣")

        for series_info in active:
            sid = series_info["series_id"]
            meta = load_meta(sid)
            if not meta:
                continue

            title       = meta.get("series_title", sid)[:45]
            category    = meta.get("category", "?")
            total_parts = meta.get("total_parts", 0)
            cat_name    = category.replace("_", " ").title()

            print("║" + f"  📖 {title}".ljust(W) + "║")
            print("║" + f"     Category: {cat_name} | Parts: {total_parts}".ljust(W) + "║")

            schedule     = meta.get("upload_schedule", {})
            parts_status = meta.get("parts_status", {})

            for pn in range(1, total_parts + 1):
                status      = parts_status.get(str(pn), "pending")
                sched_date  = schedule.get(f"part_{pn}", "")
                date_fmt    = format_date(sched_date)
                reel_exists = has_reel(sid, pn)

                if status == "uploaded":
                    # Check part status for upload date
                    ps = load_part_status(sid, pn)
                    upload_date = ""
                    if ps and ps.get("uploaded_at"):
                        upload_date = ps["uploaded_at"][:10]
                        upload_date = format_date(upload_date)
                    icon = "✅"
                    desc = f"uploaded {upload_date or date_fmt}"
                elif sched_date == today_str:
                    icon = "⏳"
                    desc = f"scheduled {date_fmt}  ← TODAY"
                    today_count += 1
                elif sched_date == tmrw_str:
                    icon = "🔜"
                    desc = f"scheduled {date_fmt}  ← TOMORROW"
                elif sched_date and sched_date < today_str:
                    icon = "⚠️ "
                    desc = f"OVERDUE {date_fmt}"
                    today_count += 1
                else:
                    icon = "🔒"
                    desc = f"scheduled {date_fmt}"

                # Reel render status
                render_tag = "📹" if reel_exists else "⬜"
                
                # Check YouTube status
                ps = load_part_status(sid, pn)
                yt_id     = ps.get("youtube_video_id", "") if ps else ""
                yt_icon   = "▶️" if yt_id else "⬛"

                line = f"     {icon} Part {pn} — {desc} {render_tag} IG·{yt_icon}YT"
                print("║" + line.ljust(W) + "║")

            print("╠" + "═" * W + "╣")

    else:
        print("║" + "  No active series".ljust(W) + "║")
        print("╠" + "═" * W + "╣")

    # ── Completed Series ──
    if completed:
        print("║" + f"  COMPLETED ({len(completed)})".ljust(W) + "║")
        print("╠" + "═" * W + "╣")
        for s in completed[-5:]:  # Show last 5
            title = s.get("series_title", s["series_id"])[:40]
            parts = s.get("total_parts", "?")
            done  = format_date(s.get("completed_at", "")[:10]) if s.get("completed_at") else "?"
            print("║" + f"  ✅ {title} ({parts} parts, done {done})".ljust(W) + "║")
        print("╠" + "═" * W + "╣")

    # ── Today's Summary ──
    if today_count > 0:
        print("║" + f"  TODAY'S UPLOADS: {today_count} part(s) ready".ljust(W) + "║")
        print("║" + f"  Run: python schedule_story_upload.py".ljust(W) + "║")
    else:
        print("║" + f"  No uploads scheduled for today ({today_str})".ljust(W) + "║")

    print("╚" + "═" * W + "╝")

    # ── Quick Stats ──
    total_active  = len(active)
    total_done    = len(completed)
    total_pending = 0
    total_uploaded = 0

    for series_info in active:
        meta = load_meta(series_info["series_id"])
        if meta:
            for s in meta.get("parts_status", {}).values():
                if s == "uploaded":
                    total_uploaded += 1
                else:
                    total_pending += 1

    print(f"\n  Stats: {total_active} active | {total_done} completed | "
          f"{total_uploaded} uploaded | {total_pending} pending")

    # ── Legend ──
    print(f"\n  Legend:")
    print(f"    ✅ = uploaded  ⏳ = today  🔜 = tomorrow  🔒 = future  ⚠️  = overdue")
    print(f"    📹 = reel rendered  ▶️ = on YouTube  ⬛ = not on YouTube")

    # ── Helpful Commands ──
    print(f"\n  Commands:")
    print(f"    python generate_story_series.py          # create new series")
    print(f"    python render_story_reels.py --all       # render pending reels")
    print(f"    python schedule_story_upload.py           # upload today's parts")
    print(f"    python schedule_story_upload.py --status  # quick status check")
    print()


if __name__ == "__main__":
    main()
