import os
import sys
import json
import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()

# Analytics tracker — log every upload for A/B performance tracking
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from analytics_tracker import log_upload as _log_upload
    _ANALYTICS_AVAILABLE = True
except ImportError:
    _ANALYTICS_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # needed for captions
]


def get_youtube_client():
    creds = None

    if os.path.exists("output/token.json"):
        creds = Credentials.from_authorized_user_file("output/token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  Token expired — refreshing...")
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("YOUTUBE_CLIENT_SECRET", "credentials.json"),
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("output/token.json", "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def get_publish_time():
    """
    Read publish time from PUBLISH_TIME_UTC environment variable.
    Set by main.py before calling this script:
      Video 1 → 9:00 AM EST (14:00 UTC) or ~15 min from now if passed
      Video 2 → 4:00 PM EST (21:00 UTC) or ~15 min from now if passed

    Falls back to 15 minutes from now if running standalone.
    """
    # ── Read from environment — set by main.py ──
    env_time = os.environ.get("PUBLISH_TIME_UTC", "").strip()

    if env_time:
        print(f"  Schedule from pipeline: {env_time}")
        return env_time

    # ── Standalone fallback — 15 minutes from now (today) ──
    fallback     = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    fallback_str = fallback.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    print(f"  Schedule fallback (standalone): {fallback_str} → ~15 min from now")
    return fallback_str


def sanitize_tags(tags):
    """
    Clean tags to satisfy YouTube Data API requirements:
    - Strip whitespace, remove empty tags
    - Remove tags with forbidden characters (<, >, ", newlines)
    - Truncate: single-word tags ≤ 30 chars, multi-word ≤ 100 chars
    - Total combined length of all tags ≤ 500 characters
    """
    import re
    cleaned = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue
        # Remove forbidden characters
        tag = re.sub(r'[<>"\r\n]', '', tag).strip()
        if not tag:
            continue
        # Truncate by word count
        if ' ' in tag:
            tag = tag[:100]
        else:
            tag = tag[:30]
        cleaned.append(tag)

    # Enforce 500-char total limit (YouTube counts chars, not tags)
    result = []
    total = 0
    for tag in cleaned:
        if total + len(tag) + 1 > 500:  # +1 for comma separator
            break
        result.append(tag)
        total += len(tag) + 1

    return result


def upload_video(youtube):
    with open("output/seo_data.json", encoding="utf-8") as f:
        seo = json.load(f)

    scheduled_time = get_publish_time()
    video_num      = os.environ.get("VIDEO_NUMBER", "1")

    # Convert UTC back to IST for display
    try:
        utc_dt  = datetime.datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%S.000Z")
        ist_dt  = utc_dt + datetime.timedelta(hours=5, minutes=30)
        ist_str = ist_dt.strftime("%d %b %Y %I:%M %p IST")
    except Exception:
        ist_str = scheduled_time

    # Use category_id from seo_data (set by 02_write_script.py based on angle type)
    # Fallback: 27 = Education (best for book/mindset content)
    category_id = str(seo.get("category_id", "27"))

    tags = sanitize_tags(seo.get("tags", []))

    body = {
        "snippet": {
            "title":       seo["youtube_title"],
            "description": seo["description"],
            "tags":        tags,
            "categoryId":  category_id,
        },
        "status": {
            "privacyStatus":           "private",
            "publishAt":               scheduled_time,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        "output/final_video.mp4",
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5
    )

    print(f"  Title     : {seo['youtube_title']}")
    print(f"  Video     : #{video_num}")
    print(f"  Publish   : {ist_str}")
    print(f"  UTC       : {scheduled_time}")
    print("  Uploading...")

    request  = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Progress  : {int(status.progress() * 100)}%", end="\r")

    video_id = response["id"]
    print(f"\n  Uploaded  : https://youtube.com/watch?v={video_id}")

    # Thumbnail — skip gracefully if channel not verified
    if os.path.exists("output/thumbnail.jpg"):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(
                    "output/thumbnail.jpg",
                    mimetype="image/jpeg"
                )
            ).execute()
            print("  Thumbnail : uploaded!")
        except Exception:
            print("  Thumbnail : skipped (verify channel at youtube.com/verify)")

    # Upload SRT captions for SEO boost (Phase 3)
    upload_srt_captions(youtube, video_id)

    # Log upload for A/B analytics tracking (Phase 6)
    if _ANALYTICS_AVAILABLE:
        _log_upload(
            video_id   = video_id,
            title      = seo["youtube_title"],
            angle_type = seo.get("angle_type", ""),
            category_id= str(seo.get("category_id", "27")),
        )

    return video_id, seo


def upload_srt_captions(youtube, video_id):
    """
    Upload SRT captions to YouTube after video upload.
    Captions indexed by YouTube search = free SEO boost.
    SRT file is already generated by 05_make_video.py at output/subtitles.srt
    """
    srt_file = "output/subtitles.srt"
    if not os.path.exists(srt_file):
        print("  Captions  : No SRT file found — skipping")
        return False

    try:
        media = MediaFileUpload(srt_file, mimetype="text/plain", resumable=False)
        youtube.captions().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId":  video_id,
                    "language": "en",
                    "name":     "English",
                    "isDraft":  False,
                }
            },
            media_body=media
        ).execute()
        print("  Captions  : SRT uploaded — captions indexed for search!")
        return True
    except Exception as e:
        print(f"  Captions  : Upload failed — {e}")
        return False


# ── Playlist helpers ──────────────────────────────────────────────────

PLAYLIST_CACHE = "output/playlist_cache.json"


def load_playlist_cache():
    """Load cached playlist name → ID mapping from disk."""
    if os.path.exists(PLAYLIST_CACHE):
        with open(PLAYLIST_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_playlist_cache(cache):
    with open(PLAYLIST_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def find_playlist_on_channel(youtube, playlist_name):
    """
    Search the authenticated channel's playlists for one matching
    `playlist_name` (case-insensitive).  Returns the playlist ID or None.
    """
    next_page = None
    while True:
        resp = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=next_page
        ).execute()

        for item in resp.get("items", []):
            if item["snippet"]["title"].strip().lower() == playlist_name.strip().lower():
                return item["id"]

        next_page = resp.get("nextPageToken")
        if not next_page:
            break
    return None


def get_or_create_playlist(youtube, playlist_name):
    """
    Return the playlist ID for `playlist_name`.
    1. Check the local cache first.
    2. If not cached, search the channel.
    3. If it doesn't exist yet, create it.
    """
    cache = load_playlist_cache()

    # 1 — cache hit
    if playlist_name in cache:
        print(f"  Playlist  : {playlist_name} (cached)")
        return cache[playlist_name]

    # 2 — search the channel
    print(f"  Searching channel for playlist \"{playlist_name}\"...")
    playlist_id = find_playlist_on_channel(youtube, playlist_name)

    if playlist_id:
        print(f"  Playlist  : found → {playlist_id}")
    else:
        # 3 — create it
        print(f"  Playlist  : not found — creating \"{playlist_name}\"...")
        body = {
            "snippet": {
                "title":       playlist_name,
                "description": f"{playlist_name} — curated by NextLevelMind."
            },
            "status": {
                "privacyStatus": "public"
            }
        }
        resp = youtube.playlists().insert(part="snippet,status", body=body).execute()
        playlist_id = resp["id"]
        print(f"  Playlist  : created → {playlist_id}")

    # persist
    cache[playlist_name] = playlist_id
    save_playlist_cache(cache)
    return playlist_id


def add_video_to_playlist(youtube, playlist_id, video_id):
    """Insert a video at the end of the given playlist."""
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind":    "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()
    print(f"  Added to playlist!")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  YouTube Uploader — NextLevelMind")
    print("=" * 50)

    if not os.path.exists("output/final_video.mp4"):
        print("\n  ERROR: output/final_video.mp4 not found!")
        return

    if not os.path.exists("output/seo_data.json"):
        print("\n  ERROR: output/seo_data.json not found!")
        return

    size_mb = os.path.getsize("output/final_video.mp4") // (1024 * 1024)
    print(f"\n  Video size: {size_mb} MB")

    print("\n  Authenticating...")
    youtube = get_youtube_client()
    print("  Authenticated!")

    print("\n  Uploading video...")
    video_id, seo = upload_video(youtube)

    # ── Auto-playlist (DISABLED by user request) ──
    print("\n  Playlist step: Disabled per user preference.")

    print("\n" + "=" * 50)
    print(f"  SUCCESS!")
    print(f"  Video ID : {video_id}")
    print(f"  URL      : https://youtube.com/shorts/{video_id}")
    print(f"  Studio   : https://studio.youtube.com")
    print("=" * 50)


if __name__ == "__main__":
    main()