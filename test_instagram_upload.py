"""
test_instagram_upload.py — Test Instagram Reel Upload via Graph API

Uploads the latest reel from reels/ directly to Instagram using the
Instagram Graph API (URL-based upload flow).

Flow:
  1. Validates / debugs the access token
  2. Finds the latest reel video + data JSON in reels/
  3. Compresses the video with ffmpeg (H.264, target ~15MB)
  4. Uploads compressed video to Tmpfiles.org (public URL, auto-deletes in 1hr)
  5. Creates a media container (media_type=REELS, video_url=<tmpfiles_url>)
  6. Polls until processing is FINISHED
  7. Publishes the reel

Prerequisites:
  - .env must have INSTAGRAM_TOKEN, INSTAGRAM_ID, INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET
  - ffmpeg must be installed and available in PATH
  - Instagram account must be Business/Creator linked to a Facebook Page
  - The Meta app must have instagram_business_content_publish permission

Usage:
  python test_instagram_upload.py                    # upload reel 1
  python test_instagram_upload.py --reel 2           # upload reel 2
  python test_instagram_upload.py --dry-run          # test without publishing
  python test_instagram_upload.py --debug-token      # only check token validity
  python test_instagram_upload.py --exchange-token   # exchange short-lived for long-lived token
  python test_instagram_upload.py --skip-compress    # skip ffmpeg compression step
"""

import os
import sys
import json
import glob
import time
import shutil
import argparse
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────
INSTAGRAM_TOKEN      = os.getenv("INSTAGRAM_TOKEN", "").strip()
INSTAGRAM_ID         = os.getenv("INSTAGRAM_ID", "").strip()
INSTAGRAM_APP_ID     = os.getenv("INSTAGRAM_APP_ID", "").strip()
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "").strip()
API_VERSION          = "v23.0"
GRAPH_API_BASE       = "https://graph.facebook.com/v23.0"
INSTAGRAM_API_BASE   = f"https://graph.instagram.com/{API_VERSION}"
REELS_FOLDER         = "reels"
TEMP_FOLDER          = "reels/temp"

# Compression settings
TARGET_SIZE_MB       = 15      # target compressed size in MB
MIN_SIZE_MB          = 5       # skip compression if already under this

# Polling config
POLL_INTERVAL        = 5       # seconds between status checks
POLL_TIMEOUT         = 300     # max seconds to wait for processing


# ── Helpers ─────────────────────────────────────────────────────

def get_latest_files(reel_num):
    """Find the latest reel files for a given reel number."""
    def latest(pattern):
        files = sorted(glob.glob(pattern))
        return files[-1] if files else None

    return {
        "video": latest(f"{REELS_FOLDER}/reel_{reel_num}_[0-9]*.mp4"),
        "cover": latest(f"{REELS_FOLDER}/reel_{reel_num}_cover_*.jpg"),
        "card":  latest(f"{REELS_FOLDER}/reel_{reel_num}_UPLOAD_CARD_*.txt"),
        "data":  latest(f"{REELS_FOLDER}/reel_{reel_num}_data_*.json"),
    }


def load_reel_data(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_caption(data):
    caption  = data.get("caption", "")
    hashtags = data.get("hashtags", "")
    if caption and hashtags:
        return f"{caption}\n\n{hashtags}"
    return caption or hashtags or "NextLevelMind 🔥"


def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f} MB"


# ── Step 0a: Compress Video ─────────────────────────────────────

def check_ffmpeg():
    """Check if ffmpeg is available in PATH."""
    if shutil.which("ffmpeg") is None:
        print("  ❌ ffmpeg not found in PATH!")
        print("     Install it from: https://ffmpeg.org/download.html")
        print("     Or run with --skip-compress to bypass compression")
        return False
    return True


def compress_video(video_path, skip_compress=False):
    """
    Compress video using ffmpeg two-pass encoding to hit TARGET_SIZE_MB.
    Returns (output_path, was_compressed).
    """
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

    if skip_compress:
        print(f"\n  ⏭️  Step 0a: Compression skipped (--skip-compress)")
        return video_path, False

    if file_size_mb <= MIN_SIZE_MB:
        print(f"\n  ⏭️  Step 0a: Compression skipped (file is only {file_size_mb:.1f}MB)")
        return video_path, False

    print(f"\n  🎞️  Step 0a: Compressing video with ffmpeg...")
    print(f"     Input:  {os.path.basename(video_path)} ({file_size_mb:.1f} MB)")
    print(f"     Target: ~{TARGET_SIZE_MB} MB")

    if not check_ffmpeg():
        print(f"     ⚠️  Skipping compression, using original file")
        return video_path, False

    os.makedirs(TEMP_FOLDER, exist_ok=True)
    base_name    = os.path.splitext(os.path.basename(video_path))[0]
    output_path  = os.path.join(TEMP_FOLDER, f"{base_name}_compressed.mp4")
    passlog_path = os.path.join(TEMP_FOLDER, "ffmpeg2pass")

    # Get video duration using ffprobe
    duration = None
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=30
        )
        duration = float(probe.stdout.strip())
    except Exception as e:
        print(f"     ⚠️  Could not probe duration ({e}), using single-pass CRF encoding")

    if duration:
        # Two-pass encoding for accurate file size targeting
        target_bits = TARGET_SIZE_MB * 1024 * 1024 * 8
        total_kbps  = int(target_bits / duration / 1000)
        audio_kbps  = 128
        video_kbps  = max(200, total_kbps - audio_kbps)

        print(f"     Duration: {duration:.1f}s | Video: {video_kbps}kbps | Audio: {audio_kbps}kbps")

        # Pass 1
        print(f"     Pass 1/2...", end="", flush=True)
        pass1 = subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-b:v", f"{video_kbps}k",
            "-pass", "1", "-passlogfile", passlog_path,
            "-an", "-f", "null", os.devnull
        ], capture_output=True, text=True)

        if pass1.returncode != 0:
            print(f" failed!\n     {pass1.stderr[-300:]}")
            return video_path, False

        print(f" done")

        # Pass 2
        print(f"     Pass 2/2...", end="", flush=True)
        start_time = time.time()
        pass2 = subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-b:v", f"{video_kbps}k",
            "-pass", "2", "-passlogfile", passlog_path,
            "-c:a", "aac", "-b:a", f"{audio_kbps}k",
            "-movflags", "+faststart",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            output_path
        ], capture_output=True, text=True)

        elapsed = time.time() - start_time

        # Clean up pass log files
        for f in glob.glob(f"{passlog_path}*"):
            try:
                os.remove(f)
            except Exception:
                pass

        if pass2.returncode != 0:
            print(f" failed!\n     {pass2.stderr[-300:]}")
            return video_path, False

        print(f" done ({elapsed:.1f}s)")

    else:
        # Fallback: single-pass CRF encoding
        print(f"     Single-pass CRF encoding...", end="", flush=True)
        start_time = time.time()
        result = subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            output_path
        ], capture_output=True, text=True)

        elapsed = time.time() - start_time

        if result.returncode != 0:
            print(f" failed!\n     {result.stderr[-300:]}")
            return video_path, False

        print(f" done ({elapsed:.1f}s)")

    # Report result
    if os.path.exists(output_path):
        out_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        reduction   = (1 - out_size_mb / file_size_mb) * 100
        print(f"  ✅ Compressed: {file_size_mb:.1f}MB → {out_size_mb:.1f}MB ({reduction:.0f}% smaller)")
        return output_path, True
    else:
        print(f"  ❌ Output file not created, using original")
        return video_path, False


def cleanup_temp(compressed_path, was_compressed):
    """Remove the temp compressed file after upload."""
    if was_compressed and compressed_path and os.path.exists(compressed_path):
        try:
            os.remove(compressed_path)
            print(f"  🗑️  Cleaned up temp file: {os.path.basename(compressed_path)}")
        except Exception as e:
            print(f"  ⚠️  Could not delete temp file: {e}")


# ── Step 0b: Upload to Tmpfiles.org ────────────────────────────

def upload_to_tmpfiles(video_path):
    """
    Upload video to tmpfiles.org and return a public direct-download URL.
    Files are automatically deleted after 1 hour.
    Returns url or None on failure.
    """
    print(f"\n  ☁️  Step 0b: Uploading to Tmpfiles.org...")

    file_size = os.path.getsize(video_path)
    print(f"     File: {os.path.basename(video_path)}")
    print(f"     Size: {format_size(file_size)}")
    print(f"     Uploading... (this may take a moment)")

    start_time = time.time()

    try:
        with open(video_path, "rb") as f:
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": (os.path.basename(video_path), f, "video/mp4")},
                timeout=300,
            )

        elapsed = time.time() - start_time
        result  = response.json()

        if response.status_code == 200 and result.get("status") == "success":
            # tmpfiles.org returns: https://tmpfiles.org/XXXXXX/filename.mp4
            # Direct download URL:  https://tmpfiles.org/dl/XXXXXX/filename.mp4
            page_url   = result["data"]["url"]
            direct_url = page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            speed      = file_size / elapsed / (1024 * 1024) if elapsed > 0 else 0

            print(f"  ✅ Uploaded! ({elapsed:.1f}s, {speed:.1f} MB/s)")
            print(f"     URL: {direct_url}")
            print(f"     ⚠️  File auto-deletes in 1 hour")
            return direct_url
        else:
            print(f"  ❌ Upload failed!")
            print(f"     Status: {response.status_code}")
            print(f"     Response: {result}")
            return None

    except requests.exceptions.Timeout:
        print(f"  ❌ Upload timed out after 5 minutes!")
        return None
    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return None


# ── Token Management ────────────────────────────────────────────

def debug_token():
    """Debug the current token to see its type, scopes, and expiration."""
    print("\n  🔍 Debugging access token...")
    print(f"     Token prefix: {INSTAGRAM_TOKEN[:20]}...")
    print(f"     Token length: {len(INSTAGRAM_TOKEN)} chars")

    # Method 1: Try debug_token endpoint (needs app token)
    if INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET:
        app_token = f"{INSTAGRAM_APP_ID}|{INSTAGRAM_APP_SECRET}"
        resp   = requests.get(f"{GRAPH_API_BASE}/debug_token", params={
            "input_token": INSTAGRAM_TOKEN, "access_token": app_token,
        })
        result = resp.json()

        if "data" in result:
            data = result["data"]
            print(f"\n  📋 Token Debug Info:")
            print(f"     Valid:   {data.get('is_valid', '?')}")
            print(f"     App ID:  {data.get('app_id', '?')}")
            print(f"     Type:    {data.get('type', '?')}")
            print(f"     User ID: {data.get('user_id', '?')}")
            scopes = data.get("scopes", data.get("granular_scopes", []))
            if scopes:
                print(f"     Scopes:  {scopes}")
            expires = data.get("expires_at", 0)
            if expires:
                import datetime
                exp_time = datetime.datetime.fromtimestamp(expires)
                print(f"     Expires: {exp_time.strftime('%Y-%m-%d %H:%M:%S')}")
                if exp_time < datetime.datetime.now():
                    print(f"     ⚠️  TOKEN IS EXPIRED!")
            if data.get("error"):
                print(f"     Error:   {data['error']}")
            return data
        elif "error" in result:
            print(f"     Debug error: {result['error'].get('message', result)}")

    # Method 2: Try /me endpoint
    print(f"\n  🔄 Trying direct /me query...")
    for base_url in [INSTAGRAM_API_BASE, GRAPH_API_BASE]:
        resp   = requests.get(f"{base_url}/me", params={"access_token": INSTAGRAM_TOKEN})
        result = resp.json()
        if "error" not in result:
            print(f"     ✅ Token works with {base_url}!")
            print(f"     Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"     ❌ {base_url}: {result['error'].get('message', '?')}")

    # Method 3: Try with IG user ID
    print(f"\n  🔄 Trying IG user ID endpoint...")
    for base_url in [INSTAGRAM_API_BASE, GRAPH_API_BASE]:
        resp = requests.get(
            f"{base_url}/{INSTAGRAM_ID}",
            params={"fields": "username,name,media_count,account_type",
                    "access_token": INSTAGRAM_TOKEN}
        )
        result = resp.json()
        if "error" not in result:
            print(f"     ✅ Works with {base_url}/{INSTAGRAM_ID}!")
            print(f"     Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"     ❌ {base_url}/{INSTAGRAM_ID}: {result['error'].get('message', '?')}")

    return None


def exchange_for_long_lived_token():
    """Exchange a short-lived token for a long-lived one (60 days)."""
    print("\n  🔄 Exchanging for long-lived token...")

    if not INSTAGRAM_APP_ID or not INSTAGRAM_APP_SECRET:
        print("  ❌ Need INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET in .env")
        return None

    # Try Facebook's exchange endpoint
    resp   = requests.get(f"{GRAPH_API_BASE}/oauth/access_token", params={
        "grant_type": "fb_exchange_token", "client_id": INSTAGRAM_APP_ID,
        "client_secret": INSTAGRAM_APP_SECRET, "fb_exchange_token": INSTAGRAM_TOKEN,
    })
    result = resp.json()

    if "access_token" in result:
        new_token = result["access_token"]
        print(f"  ✅ Got long-lived token!")
        print(f"     Expires in: {result.get('expires_in', '?')} seconds")
        print(f"\n  📋 Update your .env:\n     INSTAGRAM_TOKEN={new_token}")
        return new_token

    # Try Instagram's exchange endpoint
    print(f"  Facebook exchange failed: {result.get('error', {}).get('message', result)}")
    print(f"  🔄 Trying Instagram token exchange...")
    resp   = requests.get("https://graph.instagram.com/access_token", params={
        "grant_type": "ig_exchange_token", "client_secret": INSTAGRAM_APP_SECRET,
        "access_token": INSTAGRAM_TOKEN,
    })
    result = resp.json()

    if "access_token" in result:
        new_token  = result["access_token"]
        expires_in = result.get("expires_in", "?")
        print(f"  ✅ Got long-lived token!")
        print(f"     Expires in: {expires_in} seconds ({int(expires_in) // 86400} days)")
        print(f"\n  📋 Update your .env:\n     INSTAGRAM_TOKEN={new_token}")
        return new_token

    print(f"  ❌ Both exchanges failed: {result.get('error', {}).get('message', result)}")
    return None


def verify_token_and_get_username():
    """
    Try multiple endpoints to verify the token.
    Returns (username, working_base_url) or (None, None).
    Prefers graph.instagram.com since IGAAA tokens only work there.
    """
    print(f"\n  🔐 Verifying Instagram token...")

    endpoints = [
        (INSTAGRAM_API_BASE, f"/{INSTAGRAM_ID}", {"fields": "username,name,media_count"}),
        (INSTAGRAM_API_BASE, "/me",               {"fields": "user_id,username"}),
        (GRAPH_API_BASE,     f"/{INSTAGRAM_ID}", {"fields": "username,name,media_count"}),
        (GRAPH_API_BASE,     "/me",               {}),
    ]

    for base, path, extra_params in endpoints:
        url    = f"{base}{path}"
        params = {"access_token": INSTAGRAM_TOKEN, **extra_params}
        try:
            resp   = requests.get(url, params=params, timeout=10)
            result = resp.json()
            if "error" not in result and (
                result.get("username") or result.get("name") or result.get("id")
            ):
                username    = result.get("username", result.get("name", result.get("id", "unknown")))
                media_count = result.get("media_count", "?")
                print(f"  ✅ Authenticated as @{username} ({media_count} posts)")
                print(f"     Working endpoint: {url}")
                return username, base
        except Exception:
            pass

    return None, None


# ── Step 1: Create Container ────────────────────────────────────

def create_container(caption, video_url, base_url=None):
    """Create a media container using a public video URL."""
    print("\n  📦 Step 1: Creating media container...")

    if not base_url:
        base_url = INSTAGRAM_API_BASE

    url    = f"{base_url}/{INSTAGRAM_ID}/media"
    params = {
        "media_type":    "REELS",
        "video_url":     video_url,
        "caption":       caption,
        "share_to_feed": "true",
        "access_token":  INSTAGRAM_TOKEN,
    }

    response = requests.post(url, data=params)
    result   = response.json()

    if "error" in result:
        error = result["error"]
        print(f"  ❌ Container creation failed!")
        print(f"     Error:   {error.get('message', 'Unknown error')}")
        print(f"     Type:    {error.get('type', 'N/A')}")
        print(f"     Code:    {error.get('code', 'N/A')}")
        if error.get("error_subcode"):
            print(f"     Subcode: {error['error_subcode']}")
        return None

    container_id = result.get("id")
    if not container_id:
        print(f"  ❌ No container ID in response: {result}")
        return None

    print(f"  ✅ Container created: {container_id}")
    print(f"     Instagram is now fetching the video from Tmpfiles.org...")
    return container_id


# ── Step 2: Poll Processing Status ─────────────────────────────

def wait_for_processing(container_id, base_url=None):
    """Poll the container status until FINISHED or timeout."""
    print(f"\n  ⏳ Step 2: Waiting for Instagram to process video...")

    if not base_url:
        base_url = INSTAGRAM_API_BASE

    url    = f"{base_url}/{container_id}"
    params = {"fields": "status_code,status", "access_token": INSTAGRAM_TOKEN}

    start_time = time.time()
    attempt    = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > POLL_TIMEOUT:
            print(f"\n  ❌ Timeout after {POLL_TIMEOUT}s!")
            return False

        attempt += 1
        response = requests.get(url, params=params)
        result   = response.json()

        if "error" in result:
            print(f"\n  ❌ Status check error: {result['error'].get('message')}")
            return False

        status_code = result.get("status_code", "UNKNOWN")
        status_msg  = result.get("status", "")

        bar = "█" * (attempt % 10) + "░" * (10 - attempt % 10)
        print(f"\r     [{bar}] {status_code} ({int(elapsed)}s)", end="", flush=True)

        if status_code == "FINISHED":
            print(f"\n  ✅ Processing complete! ({int(elapsed)}s)")
            return True
        elif status_code == "ERROR":
            print(f"\n  ❌ Processing error: {status_msg}")
            return False
        elif status_code == "EXPIRED":
            print(f"\n  ❌ Container expired!")
            return False

        time.sleep(POLL_INTERVAL)


# ── Step 3: Publish ─────────────────────────────────────────────

def publish_reel(container_id, dry_run=False, base_url=None):
    """Publish the processed reel."""
    if dry_run:
        print(f"\n  🧪 Step 3: DRY RUN — skipping publish")
        print(f"     Container {container_id} is ready but NOT published")
        return "DRY_RUN"

    print(f"\n  🚀 Step 3: Publishing reel...")

    if not base_url:
        base_url = INSTAGRAM_API_BASE

    url    = f"{base_url}/{INSTAGRAM_ID}/media_publish"
    params = {"creation_id": container_id, "access_token": INSTAGRAM_TOKEN}

    response = requests.post(url, data=params)
    result   = response.json()

    if "error" in result:
        error = result["error"]
        print(f"  ❌ Publish failed!")
        print(f"     Error: {error.get('message', 'Unknown')}")
        print(f"     Code:  {error.get('code', 'N/A')}")
        return None

    media_id = result.get("id")
    if media_id:
        print(f"  ✅ REEL PUBLISHED! Media ID: {media_id}")
        return media_id
    else:
        print(f"  ❌ No media ID in response: {result}")
        return None


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload Instagram Reel via Graph API")
    parser.add_argument("--reel",           type=int, default=1, help="Reel number (default: 1)")
    parser.add_argument("--dry-run",        action="store_true", help="Do everything except publish")
    parser.add_argument("--debug-token",    action="store_true", help="Only debug the token")
    parser.add_argument("--exchange-token", action="store_true", help="Exchange for long-lived token")
    parser.add_argument("--skip-compress",  action="store_true", help="Skip ffmpeg compression")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  🎬 Instagram Reel Uploader — NextLevelMind")
    print("  Direct upload via Instagram Graph API")
    print("=" * 55)

    # ── Validate credentials ──
    if not INSTAGRAM_TOKEN:
        print("\n  ❌ INSTAGRAM_TOKEN not found in .env!")
        sys.exit(1)
    if not INSTAGRAM_ID:
        print("\n  ❌ INSTAGRAM_ID not found in .env!")
        sys.exit(1)

    print(f"\n  Instagram ID: {INSTAGRAM_ID}")
    print(f"  Token:        {INSTAGRAM_TOKEN[:20]}...{INSTAGRAM_TOKEN[-10:]}")
    print(f"  App ID:       {INSTAGRAM_APP_ID or 'not set'}")

    # ── Special modes ──
    if args.debug_token:
        debug_token()
        return

    if args.exchange_token:
        new_token = exchange_for_long_lived_token()
        if new_token:
            print(f"\n  💡 Paste the token above into .env as INSTAGRAM_TOKEN")
        return

    # ── Token diagnostics ──
    print(f"\n  {'─' * 50}")
    print(f"  Token Diagnostics")
    print(f"  {'─' * 50}")
    debug_token()

    # ── Verify token ──
    username, working_base = verify_token_and_get_username()

    if not username:
        print(f"\n  ❌ Could not authenticate with any endpoint!")
        print(f"\n  💡 Possible fixes:")
        print(f"     1. Token may be expired → run: python test_instagram_upload.py --exchange-token")
        print(f"     2. Get a new token: https://developers.facebook.com/tools/explorer/")
        print(f"        Permissions: instagram_business_basic, instagram_business_content_publish")
        print(f"     3. Ensure Instagram is a Business account linked to a Facebook Page")
        sys.exit(1)

    if args.dry_run:
        print(f"\n  Mode: DRY RUN (won't actually publish)")

    # ── Find reel files ──
    reel_num = args.reel
    files    = get_latest_files(reel_num)

    if not files["video"]:
        print(f"\n  ❌ No reel {reel_num} video found in {REELS_FOLDER}/!")
        sys.exit(1)

    video_path = files["video"]
    data       = load_reel_data(files.get("data"))
    file_size  = os.path.getsize(video_path)

    print(f"\n  📹 Reel {reel_num}: {os.path.basename(video_path)}")
    print(f"     Size:    {format_size(file_size)}")
    print(f"     Title:   {data.get('youtube_title', 'N/A')}")

    caption         = build_caption(data)
    caption_preview = caption[:100] + "..." if len(caption) > 100 else caption
    print(f"     Caption: {caption_preview}")

    # ── Confirm ──
    print(f"\n  {'─' * 50}")
    print(f"  Ready to upload Reel {reel_num} to @{username}")
    print(f"  Using: {working_base}")
    print(f"  {'─' * 50}")

    if not args.dry_run:
        confirm = input("\n  Type 'yes' to upload, or 'no' to cancel: ").strip().lower()
        if confirm not in ("yes", "y"):
            print("  Cancelled.")
            sys.exit(0)

    # ── Execute upload flow ──
    start           = time.time()
    compressed_path = None
    was_compressed  = False

    # Step 0a: Compress video with ffmpeg
    compressed_path, was_compressed = compress_video(video_path, skip_compress=args.skip_compress)

    # Step 0b: Upload to Tmpfiles.org
    video_url = upload_to_tmpfiles(compressed_path)
    if not video_url:
        print("\n  💀 Failed at Step 0b. Could not upload to Tmpfiles.org.")
        cleanup_temp(compressed_path, was_compressed)
        sys.exit(1)

    # Temp file no longer needed
    cleanup_temp(compressed_path, was_compressed)

    # Step 1: Create media container
    container_id = create_container(caption, video_url, base_url=working_base)
    if not container_id:
        print("\n  💀 Failed at Step 1. Check your token permissions.")
        print("     Need: instagram_business_content_publish")
        sys.exit(1)

    # Step 2: Wait for Instagram to process
    ready = wait_for_processing(container_id, base_url=working_base)
    if not ready:
        print("\n  💀 Failed at Step 2. Video processing error.")
        print("     Check: video codec (H.264), aspect ratio (9:16), length (3s–90s)")
        sys.exit(1)

    # Step 3: Publish
    media_id   = publish_reel(container_id, dry_run=args.dry_run, base_url=working_base)
    total_time = time.time() - start

    # ── Summary ──
    print(f"\n{'=' * 55}")
    if media_id:
        print(f"  🎉 SUCCESS! Reel uploaded to Instagram!")
        print(f"{'=' * 55}")
        print(f"  Account:  @{username}")
        print(f"  Media ID: {media_id}")
        print(f"  Video:    {os.path.basename(video_path)}")
        print(f"  Time:     {int(total_time)}s")
        print(f"\n  🔗 View at: https://www.instagram.com/{username}/")
    else:
        print(f"  ❌ Upload failed!")
        print(f"{'=' * 55}")
        print(f"  Check the error messages above for details.")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()