"""
long_07_upload.py — Long-Form YouTube Uploader

Same auth/retry logic as 07_upload.py but for long-form videos:
  - No #Shorts in title
  - Adds chapter timestamps to description (calculated from voiceover durations)
  - privacyStatus: private with publishAt (scheduled publishing)
  - Category: Education (27)
"""

import os
import sys
import re
import json
import subprocess
import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import ResumableUploadError

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from analytics_tracker import log_upload as _log_upload
    _ANALYTICS_AVAILABLE = True
except ImportError:
    _ANALYTICS_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
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
    env_time = os.environ.get("PUBLISH_TIME_UTC", "").strip()
    if env_time:
        print(f"  Schedule from pipeline: {env_time}")
        return env_time

    fallback = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    fallback_str = fallback.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    print(f"  Schedule fallback: {fallback_str}")
    return fallback_str


def sanitize_tags(tags):
    cleaned = []
    for tag in tags:
        tag = str(tag).strip().lstrip('#').strip()
        if not tag:
            continue
        tag = re.sub(r"[^a-zA-Z0-9 '\-]", '', tag).strip()
        if not tag:
            continue
        tag = tag[:100] if ' ' in tag else tag[:30]
        cleaned.append(tag)

    seen = set()
    deduped = []
    for tag in cleaned:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            deduped.append(tag)

    result = []
    total = 0
    for tag in deduped:
        cost = len(tag) + (1 if result else 0)
        if total + cost > 500:
            break
        result.append(tag)
        total += cost

    print(f"  Tags      : {len(result)} tags ({total} chars total)")
    return result


def get_audio_duration(filepath):
    """Get duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ], capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 60.0


def build_chapter_timestamps(seo):
    """
    Build YouTube chapter timestamps from voiceover section durations.

    YouTube chapter requirements:
    - First timestamp MUST be 0:00
    - At least 3 chapters
    - Each chapter must be at least 10 seconds
    - Timestamps must be in ascending order
    """
    chapter_titles = seo.get("chapter_titles", [])
    if not chapter_titles or len(chapter_titles) < 3:
        print("  Timestamps: Not enough chapters (need 3+)")
        return ""

    voiceover_dir = "output/voiceovers"
    if not os.path.exists(voiceover_dir):
        print("  Timestamps: No voiceover directory found")
        return ""

    section_files = sorted([
        f for f in os.listdir(voiceover_dir) if f.endswith(".mp3")
    ])

    if not section_files:
        print("  Timestamps: No voiceover files found")
        return ""

    # Calculate cumulative timestamps from voiceover durations
    timestamps = []
    cursor = 0.0

    # YouTube requires first timestamp to be exactly 0:00
    for i, mp3_file in enumerate(section_files):
        if i >= len(chapter_titles):
            break

        mins = int(cursor // 60)
        secs = int(cursor % 60)
        timestamps.append(f"{mins}:{secs:02d} {chapter_titles[i]}")

        dur = get_audio_duration(os.path.join(voiceover_dir, mp3_file))
        cursor += dur

    if len(timestamps) < 3:
        print(f"  Timestamps: Only {len(timestamps)} chapters — need at least 3")
        return ""

    # Validate first timestamp starts at 0:00
    if not timestamps[0].startswith("0:00"):
        timestamps[0] = "0:00 " + timestamps[0].split(" ", 1)[1]

    print(f"  Timestamps: {len(timestamps)} chapters generated")
    for ts in timestamps:
        print(f"    {ts}")

    return "\n".join(timestamps)


def upload_video(youtube):
    with open("output/seo_data.json", encoding="utf-8") as f:
        seo = json.load(f)

    scheduled_time = get_publish_time()

    # Build chapter timestamps and inject into description
    timestamps = build_chapter_timestamps(seo)
    description = seo.get("description", "")
    if timestamps and "TIMESTAMPS_PLACEHOLDER" in description:
        description = description.replace("TIMESTAMPS_PLACEHOLDER", timestamps)
    elif timestamps:
        # Insert timestamps after the first blank line
        parts = description.split("\n\n", 2)
        if len(parts) >= 2:
            description = parts[0] + "\n\n" + timestamps + "\n\n" + "\n\n".join(parts[1:])
        else:
            description = description + "\n\n" + timestamps

    # YouTube description limit is 5000 characters — truncate if needed
    if len(description) > 4900:
        description = description[:4900] + "\n..."
        print(f"  WARNING: Description truncated to 4900 chars (YouTube limit: 5000)")

    # Save updated description back
    seo["description"] = description
    with open("output/seo_data.json", "w", encoding="utf-8") as f:
        json.dump(seo, f, indent=2, ensure_ascii=False)

    try:
        utc_dt = datetime.datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M:%S.000Z")
        ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
        ist_str = ist_dt.strftime("%d %b %Y %I:%M %p IST")
    except Exception:
        ist_str = scheduled_time

    category_id = str(seo.get("category_id", "27"))
    tags = sanitize_tags(seo.get("tags", []))

    body = {
        "snippet": {
            "title":       seo["youtube_title"],
            "description": description,
            "tags":        tags,
            "categoryId":  category_id,
        },
        "status": {
            "privacyStatus":           "private",
            "publishAt":               scheduled_time,
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"  Title     : {seo['youtube_title']}")
    print(f"  Publish   : {ist_str}")
    print(f"  UTC       : {scheduled_time}")
    print(f"  Chapters  : {len(seo.get('chapter_titles', []))}")
    print("  Uploading...")

    def run_upload(upload_body):
        req = youtube.videos().insert(
            part="snippet,status",
            body=upload_body,
            media_body=MediaFileUpload(
                "output/final_video.mp4",
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024 * 5
            )
        )
        resp = None
        while resp is None:
            s, resp = req.next_chunk()
            if s:
                print(f"  Progress  : {int(s.progress() * 100)}%", end="\r")
        return resp

    # 3-attempt retry (same as Shorts uploader)
    try:
        response = run_upload(body)
    except ResumableUploadError as e:
        if "invalidTags" not in str(e):
            raise

        print(f"\n  WARNING : invalidTags — rebuilding safe tag set...")
        safe_tags = []
        total_chars = 0
        for tag in tags:
            clean = re.sub(r'[^a-z0-9]', '', tag.lower())
            if not clean or len(clean) > 30:
                continue
            cost = len(clean) + (1 if safe_tags else 0)
            if total_chars + cost > 500:
                break
            safe_tags.append(clean)
            total_chars += cost

        print(f"  Safe tags : {len(safe_tags)} tags — {safe_tags[:5]}...")
        body["snippet"]["tags"] = safe_tags
        try:
            response = run_upload(body)
        except ResumableUploadError as e2:
            if "invalidTags" in str(e2):
                print(f"\n  WARNING : still failing — uploading with no tags...")
                body["snippet"]["tags"] = []
                response = run_upload(body)
            else:
                raise

    video_id = response["id"]
    print(f"\n  Uploaded  : https://youtube.com/watch?v={video_id}")

    # Thumbnail
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

    # SRT captions
    upload_srt_captions(youtube, video_id)

    # Analytics
    if _ANALYTICS_AVAILABLE:
        _log_upload(
            video_id=video_id,
            title=seo["youtube_title"],
            angle_type="long_form",
            category_id=str(seo.get("category_id", "27")),
        )

    return video_id, seo


def upload_srt_captions(youtube, video_id):
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
        print("  Captions  : SRT uploaded — indexed for search!")
        return True
    except Exception as e:
        print(f"  Captions  : Upload failed — {e}")
        return False


def main():
    print("=" * 50)
    print("  Long-Form YouTube Uploader — NextLevelMind")
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

    print("\n  Uploading long-form video...")
    video_id, seo = upload_video(youtube)

    print("\n" + "=" * 50)
    print(f"  SUCCESS!")
    print(f"  Video ID : {video_id}")
    print(f"  URL      : https://youtube.com/watch?v={video_id}")
    print(f"  Studio   : https://studio.youtube.com")
    print("=" * 50)


if __name__ == "__main__":
    main()
