"""
scripts/analytics_tracker.py — YouTube Performance Analytics Tracker

Tracks every uploaded video and measures performance via YouTube Analytics API.
Feeds winning title patterns back into the Gemini prompt for continuous improvement.

What it does:
  1. log_upload()      — Called right after upload, saves video metadata
  2. fetch_analytics() — Pulls views/likes/CTR from YouTube Analytics API
  3. update_all()      — Updates performance for all tracked videos
  4. get_top_patterns()— Returns best-performing title patterns for Gemini context
  5. run_ab_report()   — Shows which angle (emotional vs. direct) wins per day

Usage in 07_upload.py:
    from scripts.analytics_tracker import log_upload
    log_upload(video_id, title, angle_type)

Usage in 02_write_script.py:
    from scripts.analytics_tracker import get_top_patterns
    patterns = get_top_patterns()
"""

import os
import sys
import json
import pickle
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

PERFORMANCE_LOG = "analytics_performance.json"
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Title pattern fingerprints — classify each title into a pattern bucket
TITLE_PATTERNS = [
    # Specific patterns first — order matters, first match wins
    ("nobody_told_me",    r"nobody (told|tells)"),
    ("i_wish_i_knew",     r"i wish (someone|i)"),
    ("brutal_truth",      r"brutal (truth|reality|honest)"),   # before the_lesson ("brutal" removed from there)
    ("stop_doing",        r"^stop (doing|wasting|making)"),
    ("99_percent",        r"99(%|percent)"),
    ("why_youre_losing",  r"why you.re (still|losing|struggling|broke|stuck|failing)"),
    ("one_decision",      r"(one|1) (decision|habit|choice|step|thing)"),
    ("nobody_talks",      r"nobody (talks|tells|warns|says)"),
    ("what_winners_do",   r"what (winners|successful|billionaires|top)"),
    ("how_to",            r"^how to"),
    ("youre_away",        r"you.re .* away"),
    ("the_lesson",        r"the (lesson|truth|secret|real)"),   # "brutal" removed — caught above
    ("other",             r".*"),  # catch-all
]


def _detect_pattern(title):
    """Classify a title into a pattern bucket."""
    t = title.lower()
    for name, pattern in TITLE_PATTERNS:
        if re.search(pattern, t):
            return name
    return "other"


def _load_log():
    if os.path.exists(PERFORMANCE_LOG):
        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"videos": [], "pattern_stats": {}}


def _save_log(data):
    with open(PERFORMANCE_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Log Upload ────────────────────────────────────────────────────────

def log_upload(video_id, title, angle_type="", category_id="27", seo_data=None):
    """
    Called immediately after upload. Saves video metadata to performance log.
    This is the A/B test registration step — each pair of daily videos
    is a natural A/B test (emotional vs direct advice angle).

    Args:
        video_id:    YouTube video ID
        title:       Video title
        angle_type:  "emotional storytelling" or "direct advice"
        category_id: YouTube category ID used
        seo_data:    Full seo_data dict (optional, for extra metadata)
    """
    log = _load_log()

    entry = {
        "video_id":    video_id,
        "title":       title,
        "pattern":     _detect_pattern(title),
        "angle_type":  angle_type,
        "category_id": category_id,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "views":       None,
        "likes":       None,
        "comments":    None,
        "ctr":         None,
        "avg_view_pct": None,
        "last_checked": None,
        "url":         f"https://youtube.com/shorts/{video_id}",
    }

    # Avoid duplicate logging
    existing_ids = {v["video_id"] for v in log["videos"]}
    if video_id not in existing_ids:
        log["videos"].append(entry)
        print(f"  Analytics: Logged '{title[:50]}...' (pattern: {entry['pattern']})")
    else:
        print(f"  Analytics: {video_id} already in log")

    _save_log(log)
    return entry


# ── Fetch Analytics ───────────────────────────────────────────────────

def _get_analytics_service():
    """Authenticate and build YouTube Analytics API service."""
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_file   = os.getenv("YOUTUBE_TOKEN_FILE", "youtube_token.pickle")
        secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
        creds = None

        if os.path.exists(token_file):
            with open(token_file, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(secrets_file):
                flow  = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, "wb") as f:
                    pickle.dump(creds, f)
            else:
                return None

        return build("youtubeAnalytics", "v2", credentials=creds)

    except Exception as e:
        print(f"  Analytics: Auth failed — {e}")
        return None


def fetch_analytics(video_id, days_back=30):
    """
    Pull views, likes, comments, and estimatedMinutesWatched
    from YouTube Analytics API for one video.

    Returns dict with metrics or None on failure.
    """
    service = _get_analytics_service()
    if not service:
        return None

    end_date   = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        resp = service.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,likes,comments,estimatedMinutesWatched,averageViewDuration",
            dimensions="video",
            filters=f"video=={video_id}",
            sort="-views",
            maxResults=1,
        ).execute()

        rows = resp.get("rows", [])
        if not rows:
            return {"views": 0, "likes": 0, "comments": 0, "watch_minutes": 0, "avg_view_sec": 0}

        row = rows[0]
        return {
            "views":         int(row[1]),
            "likes":         int(row[2]),
            "comments":      int(row[3]),
            "watch_minutes": float(row[4]),
            "avg_view_sec":  float(row[5]),
        }

    except Exception as e:
        print(f"  Analytics: Failed to fetch {video_id} — {e}")
        return None


# ── Update All Videos ─────────────────────────────────────────────────

def update_all(max_videos=50, min_age_hours=24):
    """
    Refresh analytics for all logged videos.
    Only checks videos that are at least min_age_hours old.

    Args:
        max_videos:    Maximum number of videos to check per run
        min_age_hours: Skip videos uploaded less than this many hours ago
    """
    log   = _load_log()
    now   = datetime.now()
    count = 0

    for entry in log["videos"][-max_videos:]:
        try:
            uploaded = datetime.fromisoformat(entry["uploaded_at"])
        except Exception:
            continue

        age_hours = (now - uploaded).total_seconds() / 3600
        if age_hours < min_age_hours:
            continue

        metrics = fetch_analytics(entry["video_id"])
        if metrics:
            entry["views"]        = metrics["views"]
            entry["likes"]        = metrics["likes"]
            entry["comments"]     = metrics["comments"]
            entry["avg_view_sec"] = metrics.get("avg_view_sec", 0)
            entry["last_checked"] = now.isoformat(timespec="seconds")
            count += 1

    # Recalculate pattern stats
    _recalculate_pattern_stats(log)
    _save_log(log)
    print(f"  Analytics: Updated {count} videos")
    return count


def _recalculate_pattern_stats(log):
    """Aggregate performance by title pattern and angle type."""
    stats = {}

    for entry in log["videos"]:
        if entry.get("views") is None:
            continue

        pattern = entry.get("pattern", "other")
        angle   = entry.get("angle_type", "unknown")
        views   = entry["views"]
        likes   = entry.get("likes") or 0

        key = pattern
        if key not in stats:
            stats[key] = {
                "pattern":   pattern,
                "count":     0,
                "total_views": 0,
                "total_likes": 0,
                "avg_views": 0,
                "best_title": "",
                "best_views": 0,
                "angles":    {},
            }

        s = stats[key]
        s["count"]       += 1
        s["total_views"] += views
        s["total_likes"] += likes
        s["avg_views"]    = s["total_views"] // s["count"] if s["count"] else 0

        if views > s["best_views"]:
            s["best_views"] = views
            s["best_title"] = entry["title"]

        s["angles"][angle] = s["angles"].get(angle, 0) + views

    log["pattern_stats"] = stats


# ── Get Top Patterns ─────────────────────────────────────────────────

def get_top_patterns(top_n=3):
    """
    Return the top N performing title patterns sorted by average views.
    Used to inject into the Gemini prompt for A/B-informed generation.

    Returns:
        List of dicts: [{"pattern": str, "avg_views": int, "best_title": str}]
        Empty list if not enough data yet.
    """
    log   = _load_log()
    stats = log.get("pattern_stats", {})

    # Filter: only patterns with at least 2 videos (enough signal)
    valid = [s for s in stats.values() if s["count"] >= 2]
    if not valid:
        return []

    ranked = sorted(valid, key=lambda x: x["avg_views"], reverse=True)
    return [
        {
            "pattern":    r["pattern"],
            "avg_views":  r["avg_views"],
            "best_title": r["best_title"],
        }
        for r in ranked[:top_n]
    ]


# ── A/B Report ────────────────────────────────────────────────────────

def run_ab_report():
    """
    Print a human-readable A/B performance report.
    Compares emotional storytelling vs direct advice angles.
    """
    log = _load_log()
    videos = [v for v in log["videos"] if v.get("views") is not None]

    if len(videos) < 4:
        print("  A/B Report: Not enough data yet (need at least 4 videos with views)")
        return

    angle_stats = {}
    for v in videos:
        angle = v.get("angle_type", "unknown")
        if angle not in angle_stats:
            angle_stats[angle] = {"count": 0, "total_views": 0, "titles": []}
        angle_stats[angle]["count"]       += 1
        angle_stats[angle]["total_views"] += v["views"]
        angle_stats[angle]["titles"].append((v["title"], v["views"]))

    print("\n" + "=" * 55)
    print("  A/B PERFORMANCE REPORT")
    print("=" * 55)

    for angle, data in sorted(angle_stats.items(),
                              key=lambda x: x[1]["total_views"], reverse=True):
        avg = data["total_views"] // data["count"] if data["count"] else 0
        print(f"\n  Angle: {angle}")
        print(f"  Videos: {data['count']}  |  Avg views: {avg:,}")
        # Best title
        best = sorted(data["titles"], key=lambda x: x[1], reverse=True)[0]
        print(f"  Best:   \"{best[0][:60]}\" ({best[1]:,} views)")

    # Pattern leaderboard
    stats = log.get("pattern_stats", {})
    if stats:
        print("\n  TOP TITLE PATTERNS BY AVERAGE VIEWS:")
        ranked = sorted(stats.values(), key=lambda x: x["avg_views"], reverse=True)
        for i, r in enumerate(ranked[:5], 1):
            if r["count"] >= 1:
                print(f"  {i}. [{r['pattern']}] avg {r['avg_views']:,} views "
                      f"({r['count']} videos)")
                print(f"     Best: \"{r['best_title'][:55]}\"")

    print("\n" + "=" * 55)


# ── CLI Entry Point ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Analytics Tracker")
    parser.add_argument("--update", action="store_true",
                        help="Fetch latest analytics for all logged videos")
    parser.add_argument("--report", action="store_true",
                        help="Print A/B performance report")
    parser.add_argument("--patterns", action="store_true",
                        help="Show top performing title patterns")
    args = parser.parse_args()

    if args.update:
        print("Updating analytics for all videos...")
        update_all()
        print("Done!")

    if args.report:
        run_ab_report()

    if args.patterns:
        patterns = get_top_patterns()
        if patterns:
            print("\nTop performing title patterns:")
            for p in patterns:
                print(f"  [{p['pattern']}] avg {p['avg_views']:,} views")
                print(f"    Best: \"{p['best_title']}\"")
        else:
            print("Not enough data yet — keep uploading!")

    if not any(vars(args).values()):
        parser.print_help()
