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
import sys
import pickle
import time
from datetime import datetime
from dotenv import load_dotenv

# Trending tag injector (Phase 5)
_scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _scripts_dir)
try:
    from get_trending_tags import get_trending_tags as _get_trending_tags
    _TRENDING_AVAILABLE = True
except ImportError:
    _TRENDING_AVAILABLE = False

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
    cat_key      = series_meta.get("category", "")
    script_hook  = part_script.get("hook", "")
    cliffhanger  = part_script.get("cliffhanger", "")

    # ── Title (under 60 chars for mobile, #Shorts at end) ───────
    # Format: "Series Title Part X/Y — Hook Preview #Shorts"
    base_title = f"{series_title} | Part {part_num}/{total_parts} #Shorts"
    if len(base_title) < 55 and script_hook:
        hook_preview = script_hook[:30].rstrip()
        candidate    = f"{series_title} — {hook_preview} #Shorts"
        title        = candidate if len(candidate) <= 60 else base_title
    else:
        title = base_title[:97]  # API hard limit 100

    # ── Keyword phrases per category for first 2 SEO lines ───────
    category_seo_lines = {
        "discipline_habits": (
            "Daily discipline habits that separate the top 1% from everyone else",
            "Self discipline tips | The morning routine habit 90% of people skip"
        ),
        "mental_strength": (
            "How to build unbreakable mental strength when life gets hard",
            "Mental toughness training | What winners do that nobody ever talks about"
        ),
        "success_mindset": (
            "The success mindset secrets billionaires use every single day",
            "Wealth mindset & growth habits | Why 95% of people stay stuck forever"
        ),
        "life_philosophy": (
            "Stoic life philosophy that will completely rewire how you think",
            "Stoicism & purpose | Ancient wisdom that modern self-help ignores"
        ),
        "overcoming_failure": (
            "How to overcome failure and bounce back stronger than before",
            "Resilience mindset | The comeback strategy that actually works"
        ),
        "focus_productivity": (
            "Deep work and focus habits that 10x your output every single day",
            "Productivity secrets | How to eliminate distractions and enter flow state"
        ),
    }
    seo_line1, seo_line2 = category_seo_lines.get(
        cat_key,
        (
            "Daily mindset and self-improvement content that actually changes lives",
            "Success habits & motivation | What the top 1% do differently every day"
        )
    )

    # ── Description ─────────────────────────────────────────────
    # First 2 lines are the SEO goldmine — keyword-rich, no emojis
    ig_caption = part_script.get("caption", "")
    cta        = part_script.get("cta", "").replace("Comment", "Comment below")

    desc_lines = [
        seo_line1,
        seo_line2,
        "",
    ]

    if script_hook:
        desc_lines.append(script_hook)
        desc_lines.append("")

    if ig_caption:
        desc_lines.append(ig_caption)
        desc_lines.append("")

    desc_lines.append(f"📖 {series_title} — Part {part_num} of {total_parts}")
    if part_num > 1:
        desc_lines.append(f"   ← Watch Part {part_num - 1} first for full context!")
    if part_num < total_parts:
        desc_lines.append(f"   🔔 Part {part_num + 1} drops tomorrow — subscribe so you don't miss it")
    desc_lines.append("")

    if cliffhanger and part_num < total_parts:
        desc_lines.append(f"🎯 Coming next: {cliffhanger}")
        desc_lines.append("")

    if cta:
        desc_lines.append(cta)
        desc_lines.append("")

    desc_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    desc_lines.append("Follow @nextlevelmind for daily mindset content that hits different.")
    desc_lines.append("🔔 Subscribe — new short every single day")
    desc_lines.append("👍 Like if this hit different")
    desc_lines.append("💾 Save this for when you need it most")
    desc_lines.append("📌 Share with someone who needs to hear this")
    desc_lines.append("")

    # ── Hashtag block — first hashtag becomes video's label on Shorts feed
    hashtag_map = {
        "discipline_habits":  "#Shorts #YouTubeShorts #discipline #selfimprovement #dailyhabits #morningroutine #mindset #consistency #motivation #selfcontrol",
        "mental_strength":    "#Shorts #YouTubeShorts #mentalstrength #mentaltoughness #mindset #selfimprovement #resilience #motivation #innerstrength #personaldevelopment",
        "success_mindset":    "#Shorts #YouTubeShorts #successmindset #growthmindset #wealthmindset #motivation #billionairehabits #selfimprovement #mindset #success",
        "life_philosophy":    "#Shorts #YouTubeShorts #stoicism #lifephilosophy #mindset #motivation #selfimprovement #stoicwisdom #personaldevelopment #purposedriven",
        "overcoming_failure": "#Shorts #YouTubeShorts #motivation #nevergiveuup #resilience #overcomingfailure #mindset #selfimprovement #bouneback #success",
        "focus_productivity": "#Shorts #YouTubeShorts #productivity #deepwork #focus #timemanagement #selfimprovement #mindset #discipline #flowstate",
    }
    hashtags = hashtag_map.get(
        cat_key,
        "#Shorts #YouTubeShorts #motivation #mindset #selfimprovement #discipline #success #personaldevelopment #growthmindset #inspiration"
    )
    desc_lines.append(hashtags)
    desc_lines.append("#nextlevelmind #motivationalvideo #storytime #successhabits #mentalhealth")

    description = "\n".join(desc_lines)

    # ── Tags (30+ search-optimized) ──────────────────────────────
    category_tags = {
        "discipline_habits": [
            "discipline", "daily habits", "morning routine", "self discipline",
            "consistency", "willpower", "good habits", "how to be disciplined",
            "self control", "discipline mindset", "build discipline",
            "morning routine for success", "daily routine", "habits for success",
            "how to build habits", "discipline tips", "self improvement habits",
        ],
        "mental_strength": [
            "mental strength", "mental toughness", "overcome anxiety",
            "build resilience", "inner strength", "mindset shift",
            "how to be mentally strong", "mental health tips",
            "emotional intelligence", "overcome fear", "mental health motivation",
            "how to deal with stress", "positive mindset", "mental fortitude",
            "overcome challenges", "mindset training", "stress management",
        ],
        "success_mindset": [
            "success mindset", "billionaire habits", "wealth mindset",
            "growth mindset", "think like a winner", "millionaire mindset",
            "success habits", "how to be successful", "success secrets",
            "entrepreneur mindset", "self made success", "financial mindset",
            "abundance mindset", "goal setting", "success tips 2024",
            "how to think like a billionaire", "winner mindset",
        ],
        "life_philosophy": [
            "stoicism", "life philosophy", "find your purpose",
            "intentional living", "stoic wisdom", "stoic mindset",
            "marcus aurelius", "epictetus", "modern stoicism",
            "life lessons", "wisdom quotes", "philosophical mindset",
            "meaning of life", "living with purpose", "stoicism 2024",
            "stoic philosophy", "life changing wisdom",
        ],
        "overcoming_failure": [
            "overcoming failure", "bounce back", "resilience",
            "starting over", "failure to success", "never give up",
            "comeback mindset", "success after failure", "how to get back up",
            "dealing with failure", "turning failure into success",
            "overcome setbacks", "perseverance", "keep going motivation",
            "rise after failure", "grit and determination", "never quit",
        ],
        "focus_productivity": [
            "focus", "deep work", "eliminate distractions",
            "flow state", "productivity", "get more done",
            "productivity tips", "how to focus better", "time management",
            "work smarter", "concentration tips", "digital detox",
            "productivity hacks", "cal newport", "deep work tips",
            "how to be productive", "focus techniques",
        ],
    }

    cat_tags = category_tags.get(cat_key, [])

    # High-traffic evergreen tags always included
    viral_reference_tags = [
        "atomic habits", "david goggins", "stoicism", "alex hormozi",
        "james clear", "jocko willink", "self improvement",
    ]

    base_tags = [
        "shorts", "youtubeshorts", "nextlevelmind", "motivation", "mindset",
        "inspiration", "selfimprovement", "personaldevelopment",
        "motivationalvideo", "selfhelp", "personalgrowth",
        f"part{part_num}of{total_parts}",
        series_title.lower().replace(" ", "")[:30],
    ]

    tags = list(dict.fromkeys(base_tags + cat_tags + viral_reference_tags))

    # Inject trending tags (Phase 5)
    if _TRENDING_AVAILABLE:
        trending = _get_trending_tags(category=cat_key if cat_key else "general")
        existing_lower = {t.lower() for t in tags}
        for t in trending:
            if t.lower() not in existing_lower:
                tags.append(t)
                existing_lower.add(t.lower())

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
            "categoryId":  "27",  # Education — correct for book/mindset content
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
