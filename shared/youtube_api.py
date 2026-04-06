"""
shared/youtube_api.py — YouTube Data API v3 upload functions
Used by schedule_story_upload.py to upload reels as YouTube Shorts.

YouTube OAuth Setup:
1. Go to https://console.cloud.google.com
2. Create/select project → Enable "YouTube Data API v3"
3. Credentials → Create OAuth 2.0 Client ID → Desktop App
4. Download JSON → save as client_secrets.json in project root
5. First run will open browser for Google login
6. Token saved to youtube_token.pickle for future runs
"""

import os
import pickle
import time
from datetime import datetime
from dotenv import load_dotenv

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # needed for comments
]

CLIENT_SECRETS = os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secrets.json")
TOKEN_FILE     = os.getenv("YOUTUBE_TOKEN_FILE", "youtube_token.pickle")
CHANNEL_ID     = os.getenv("YOUTUBE_CHANNEL_ID", "")


# ── Auth ──────────────────────────────────────────────────────

def get_youtube_service():
    """
    Authenticate and return a YouTube API service instance.
    Handles token refresh and first-time browser auth automatically.
    Returns service or None on failure.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  🔄 Refreshing YouTube token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  ⚠️  Token refresh failed: {e} — re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRETS):
                print(f"  ❌ {CLIENT_SECRETS} not found!")
                print(f"     Download from: https://console.cloud.google.com")
                print(f"     Credentials → OAuth 2.0 → Desktop App → Download JSON")
                return None
            print("  🌐 Opening browser for YouTube authentication...")
            flow  = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("  ✅ YouTube token saved")

    return build("youtube", "v3", credentials=creds)


# ── Title & Description Builder ───────────────────────────────

def build_youtube_metadata(part_script, series_meta, part_num, total_parts):
    """
    Build YouTube-optimized title, description, and tags for a Short.
    """
    series_title = series_meta.get("series_title", "")
    category     = series_meta.get("category", "").replace("_", " ").title()
    script_hook  = part_script.get("hook", "")
    cliffhanger  = part_script.get("cliffhanger", "")

    # ── Title (under 100 chars) ──────────────────────────────────
    base_title = f"{series_title} | Part {part_num}/{total_parts}"
    if len(base_title) < 80 and script_hook:
        hook_preview = script_hook[:50].rstrip()
        candidate    = f"{base_title} — {hook_preview}"
        title        = candidate if len(candidate) <= 100 else base_title
    else:
        title = base_title[:100]

    # ── Description ─────────────────────────────────────────────
    ig_caption = part_script.get("caption", "")
    cta        = part_script.get("cta", "").replace("Comment", "Comment below")

    desc_lines = []

    if script_hook:
        desc_lines.append(script_hook)
        desc_lines.append("")

    if ig_caption:
        desc_lines.append(ig_caption)
        desc_lines.append("")

    desc_lines.append(f"📖 {series_title}")
    desc_lines.append(f"   This is Part {part_num} of {total_parts}")
    if part_num > 1:
        desc_lines.append(f"   ← Watch Part {part_num - 1} first!")
    if part_num < total_parts:
        desc_lines.append(f"   Part {part_num + 1} drops tomorrow 🔔")
    desc_lines.append("")

    if cliffhanger and part_num < total_parts:
        desc_lines.append(f"🎯 Coming up: {cliffhanger}")
        desc_lines.append("")

    if cta:
        desc_lines.append(cta)
        desc_lines.append("")

    desc_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    desc_lines.append("🔔 Subscribe for daily mindset content")
    desc_lines.append("👍 Like if this hit different")
    desc_lines.append("💾 Save this for when you need it most")
    desc_lines.append("")
    desc_lines.append("#Shorts #YouTubeShorts #nextlevelmind")

    description = "\n".join(desc_lines)

    # ── Tags (search-optimized) ──────────────────────────────────
    category_tags = {
        "discipline_habits":  ["discipline", "daily habits", "morning routine",
                               "self discipline", "consistency", "willpower"],
        "mental_strength":    ["mental strength", "mental toughness", "overcome anxiety",
                               "build resilience", "mindset", "inner strength"],
        "success_mindset":    ["success mindset", "billionaire habits", "wealth mindset",
                               "growth mindset", "think like a winner", "career growth"],
        "life_philosophy":    ["stoicism", "life philosophy", "find your purpose",
                               "intentional living", "stoic wisdom"],
        "overcoming_failure": ["overcoming failure", "bounce back", "resilience",
                               "starting over", "failure to success", "never give up"],
        "focus_productivity": ["focus", "deep work", "eliminate distractions",
                               "flow state", "productivity", "get more done"],
    }

    cat_key  = series_meta.get("category", "")
    cat_tags = category_tags.get(cat_key, [])

    base_tags = [
        "nextlevelmind", "motivation", "shorts", "mindset",
        "inspiration", "selfimprovement", "personaldevelopment",
        "motivationalvideo", "storytime",
        f"part{part_num}of{total_parts}",
        series_title.lower().replace(" ", ""),
    ]

    tags = list(dict.fromkeys(base_tags + cat_tags))  # deduplicate, preserve order
    return title, description, tags


# ── Playlist Management ───────────────────────────────────────

def get_or_create_playlist(service, series_meta):
    """
    Find existing playlist for this series or create a new one.
    Returns playlist_id or None.
    """
    series_title = series_meta.get("series_title", "Story Series")
    category     = series_meta.get("category", "").replace("_", " ").title()
    total_parts  = series_meta.get("total_parts", 0)

    try:
        resp = service.playlists().list(
            part="snippet", mine=True, maxResults=50
        ).execute()

        for pl in resp.get("items", []):
            if pl["snippet"]["title"] == series_title:
                pl_id = pl["id"]
                print(f"  📋 Using existing playlist: {series_title} ({pl_id})")
                return pl_id

        # Create new playlist
        created = service.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title":       series_title,
                    "description": (
                        f"A {total_parts}-part story series from @NextLevelMind\n"
                        f"Category: {category}\n\n"
                        f"New parts drop daily — subscribe and hit the bell 🔔"
                    ),
                    "tags": ["nextlevelmind", "series", "motivation", category.lower()],
                },
                "status": {"privacyStatus": "public"}
            }
        ).execute()

        pl_id = created["id"]
        print(f"  ✅ Created playlist: {series_title} ({pl_id})")
        return pl_id

    except HttpError as e:
        print(f"  ⚠️  Playlist error: {e} — continuing without playlist")
        return None


def add_to_playlist(service, video_id, playlist_id, part_num):
    """Add a video to a playlist at the correct position."""
    try:
        service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    "position":   part_num - 1,  # 0-indexed
                }
            }
        ).execute()
        print(f"  ✅ Added to playlist at position {part_num}")
        return True
    except HttpError as e:
        print(f"  ⚠️  Could not add to playlist: {e}")
        return False


# ── Upload Video ─────────────────────────────────────────────

def upload_short(service, video_path, title, description, tags,
                 part_num, total_parts):
    """
    Upload a video as a YouTube Short.
    Returns video_id or None on failure.
    """
    print(f"\n  📤 Uploading to YouTube Shorts...")
    print(f"     Title: {title}")

    file_size = os.path.getsize(video_path)
    print(f"     File:  {os.path.basename(video_path)} ({file_size / (1024*1024):.1f}MB)")

    body = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        tags,
            "categoryId":  "26",  # Howto & Style — best for motivation content
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5  # 5MB chunks
    )

    try:
        request    = service.videos().insert(
            part="snippet,status", body=body, media_body=media
        )
        response   = None
        start_time = time.time()

        print(f"     Uploading...", end="", flush=True)
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"\r     Uploading... {pct}%", end="", flush=True)
        print()

        elapsed  = time.time() - start_time
        video_id = response.get("id")

        if video_id:
            speed = file_size / elapsed / (1024 * 1024) if elapsed > 0 else 0
            print(f"  ✅ Uploaded! ({elapsed:.1f}s, {speed:.1f} MB/s)")
            print(f"     Video ID: {video_id}")
            print(f"     URL: https://youtube.com/shorts/{video_id}")
            return video_id
        else:
            print(f"  ❌ No video ID in response")
            return None

    except HttpError as e:
        print(f"\n  ❌ YouTube upload error: {e}")
        return None
    except Exception as e:
        print(f"\n  ❌ Unexpected error: {e}")
        return None


# ── Post + Pin Comment ────────────────────────────────────────

def pin_part_comment(service, video_id, part_num, total_parts, series_title):
    """
    Post and pin a comment driving viewers to the next part.
    """
    if part_num >= total_parts:
        comment_text = (
            f"🎬 This is the FINAL part of \"{series_title}\"!\n\n"
            f"💬 Comment your biggest takeaway below 👇\n"
            f"🔔 Subscribe for new story series every week\n"
            f"📖 Watch the full series from Part 1 on our channel!"
        )
    else:
        comment_text = (
            f"👇 Part {part_num + 1} drops TOMORROW!\n\n"
            f"🔔 Subscribe + hit the bell so you don't miss it\n"
            f"💬 Comment 'PART {part_num + 1}' if you want to know what happens next\n"
            f"📖 This is Part {part_num} of {total_parts} in \"{series_title}\""
        )

    try:
        comment_resp = service.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": comment_text}
                    }
                }
            }
        ).execute()

        comment_id = comment_resp["snippet"]["topLevelComment"]["id"]
        print(f"  💬 Comment posted ✅")
        return comment_id

    except HttpError as e:
        print(f"  ⚠️  Comment/pin failed: {e} — video still uploaded successfully")
        return None
    except Exception as e:
        print(f"  ⚠️  Comment error: {e} — video still uploaded successfully")
        return None


# ── Main Upload Function ──────────────────────────────────────

def upload_part_to_youtube(video_path, part_script, series_meta,
                           part_num, total_parts, dry_run=False):
    """
    Full YouTube Shorts upload flow for one story part.
    Returns dict with video_id, playlist_id, comment_id or None on failure.
    YouTube failures are always non-fatal — caller must handle None gracefully.
    """
    print(f"\n  {'─' * 45}")
    print(f"  🎬 YouTube Shorts Upload")
    print(f"  {'─' * 45}")

    if dry_run:
        title, _, tags = build_youtube_metadata(
            part_script, series_meta, part_num, total_parts
        )
        print(f"  🧪 DRY RUN — skipping YouTube upload")
        print(f"     Title: {title}")
        print(f"     Tags:  {tags[:5]}...")
        return {"dry_run": True, "video_id": None}

    service = get_youtube_service()
    if not service:
        print(f"  ❌ Could not authenticate with YouTube")
        return None

    title, description, tags = build_youtube_metadata(
        part_script, series_meta, part_num, total_parts
    )
    print(f"  Title: {title}")

    playlist_id = get_or_create_playlist(service, series_meta)

    video_id = upload_short(
        service, video_path, title, description, tags, part_num, total_parts
    )
    if not video_id:
        return None

    if playlist_id:
        add_to_playlist(service, video_id, playlist_id, part_num)

    comment_id = pin_part_comment(
        service, video_id, part_num, total_parts,
        series_meta.get("series_title", "")
    )

    return {
        "video_id":    video_id,
        "playlist_id": playlist_id,
        "comment_id":  comment_id,
        "url":         f"https://youtube.com/shorts/{video_id}",
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
    }
