import os
import time
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import (
    YOUTUBE_CLIENT_SECRETS_RK, YOUTUBE_TOKEN_RK,
    YOUTUBE_SCOPES, YOUTUBE_CATEGORY_ID,
)


def get_youtube_service():
    """
    Authenticate with YouTube API using separate OAuth credentials
    for the Radha Krishna channel. Token stored at token_rk.json.
    """
    creds = None

    if os.path.exists(YOUTUBE_TOKEN_RK):
        with open(YOUTUBE_TOKEN_RK, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  Refreshing YouTube token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  Token refresh failed: {e} — re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_RK):
                raise FileNotFoundError(
                    f"OAuth client secrets not found: {YOUTUBE_CLIENT_SECRETS_RK}\n"
                    "Download from Google Cloud Console and place it there."
                )
            print("  Opening browser for YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS_RK, YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(YOUTUBE_TOKEN_RK, "wb") as f:
            pickle.dump(creds, f)
        print("  YouTube token saved")

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title, description, tags):
    """
    Upload video to the Radha Krishna YouTube channel.
    Returns video_id on success.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    service = get_youtube_service()

    file_size = os.path.getsize(video_path)
    print(f"  File: {os.path.basename(video_path)} ({file_size / (1024 * 1024):.1f}MB)")

    clean_tags = _sanitize_tags(tags)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": clean_tags,
            "categoryId": YOUTUBE_CATEGORY_ID,
            "defaultLanguage": "hi",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,
    )

    request = service.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    start = time.time()
    print("  Uploading...", end="", flush=True)

    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"\r  Uploading... {pct}%", end="", flush=True)

    elapsed = time.time() - start
    video_id = response.get("id", "")
    print(f"\r  Upload complete in {elapsed:.0f}s")
    print(f"  Video ID: {video_id}")
    print(f"  URL: https://youtube.com/watch?v={video_id}")

    return video_id


def _sanitize_tags(tags):
    clean = []
    total_len = 0
    for tag in tags:
        tag = tag.strip().lstrip("#")
        tag = "".join(c for c in tag if c.isalnum() or c in " -'")
        tag = tag.strip()
        if not tag:
            continue
        if len(tag) > 30 and " " not in tag:
            tag = tag[:30]
        elif len(tag) > 100:
            tag = tag[:100]
        if total_len + len(tag) > 500:
            break
        clean.append(tag)
        total_len += len(tag)
    return clean


if __name__ == "__main__":
    service = get_youtube_service()
    print("  YouTube auth successful!")
