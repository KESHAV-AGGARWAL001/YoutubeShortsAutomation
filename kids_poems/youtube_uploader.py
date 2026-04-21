"""
youtube_uploader.py — YouTube Uploader for Kids Poems Channel

Uploads with selfDeclaredMadeForKids=True (critical for kids algorithm).
Uses separate OAuth credentials from other channels.
"""

import os
import sys
import re
import time
import pickle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    YOUTUBE_CLIENT_SECRETS_KP, YOUTUBE_TOKEN_KP,
    YOUTUBE_SCOPES, YOUTUBE_CATEGORY_ID,
)

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_youtube_service():
    """Authenticate with YouTube API using kids channel credentials."""
    creds = None

    if os.path.exists(YOUTUBE_TOKEN_KP):
        with open(YOUTUBE_TOKEN_KP, "rb") as f:
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
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_KP):
                raise FileNotFoundError(
                    f"OAuth client secrets not found: {YOUTUBE_CLIENT_SECRETS_KP}\n"
                    "Download from Google Cloud Console and place it in kids_poems/"
                )
            print("  Opening browser for YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS_KP, YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(YOUTUBE_TOKEN_KP, "wb") as f:
            pickle.dump(creds, f)
        print("  YouTube token saved")

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title, description, tags, schedule_utc=None):
    """
    Upload video to the kids YouTube channel.
    Made for Kids = True (unlocks kids algorithm).
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    service = get_youtube_service()

    file_size = os.path.getsize(video_path)
    print(f"  File: {os.path.basename(video_path)} ({file_size / (1024 * 1024):.1f}MB)")

    clean_tags = _sanitize_tags(tags)

    status = {
        "selfDeclaredMadeForKids": True,
        "madeForKids": True,
    }

    if schedule_utc:
        status["privacyStatus"] = "private"
        status["publishAt"] = schedule_utc
    else:
        status["privacyStatus"] = "public"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": clean_tags,
            "categoryId": YOUTUBE_CATEGORY_ID,
            "defaultLanguage": "en",
        },
        "status": status,
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
        status_obj, response = request.next_chunk()
        if status_obj:
            pct = int(status_obj.progress() * 100)
            print(f"\r  Uploading... {pct}%", end="", flush=True)

    elapsed = time.time() - start
    video_id = response.get("id", "")
    print(f"\r  Upload complete in {elapsed:.0f}s")
    print(f"  Video ID: {video_id}")
    print(f"  URL: https://youtube.com/shorts/{video_id}")

    return video_id


def _sanitize_tags(tags):
    clean = []
    total_len = 0
    for tag in tags:
        tag = str(tag).strip().lstrip("#")
        tag = re.sub(r"[^a-zA-Z0-9 '\-]", '', tag).strip()
        if not tag:
            continue
        tag = tag[:100] if ' ' in tag else tag[:30]
        if total_len + len(tag) > 500:
            break
        clean.append(tag)
        total_len += len(tag)
    return clean


if __name__ == "__main__":
    service = get_youtube_service()
    print("  YouTube auth successful!")
