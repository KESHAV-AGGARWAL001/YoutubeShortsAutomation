"""
download_music.py — Free Music Downloader for Kids Poems

Downloads copyright-free music from Freesound.org organized by mood.
All tracks are Creative Commons 0 (CC0) — free for commercial use,
no attribution required, safe for YouTube monetization.

Prerequisites:
  1. Create a free account at https://freesound.org/home/register/
  2. Get API key at https://freesound.org/apiv2/apply/
     (select "APIv2 key", any description works)
  3. Add to kids_poems/.env:  FREESOUND_API_KEY=your_key_here

Usage:
  python download_music.py                   # Download all moods
  python download_music.py --mood calm       # Download one mood only
  python download_music.py --limit 15        # More tracks per search term
  python download_music.py --list            # List available moods + terms
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, "music")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")
API_BASE = "https://freesound.org/apiv2"

SEARCH_TERMS = {
    "upbeat": [
        "happy children music",
        "kids fun melody",
        "upbeat cartoon music",
        "cheerful ukulele kids",
        "energetic xylophone children",
        "playful clapping music",
        "bouncy kids song instrumental",
    ],
    "calm": [
        "lullaby music box",
        "gentle piano lullaby",
        "soft kids bedtime music",
        "calm music box melody",
        "sleeping baby music",
        "peaceful harp children",
        "soothing bells lullaby",
    ],
    "playful": [
        "cheerful glockenspiel kids",
        "playful marimba children",
        "funny cartoon music",
        "happy whistle melody",
        "kids toy piano music",
        "bouncy pizzicato strings",
        "cheerful recorder melody",
    ],
    "magical": [
        "magical fairy music",
        "dreamy celesta melody",
        "whimsical music box fairy",
        "enchanted harp children",
        "sparkle chime magical",
        "fantasy bells dreamy",
        "fairy tale orchestra gentle",
    ],
}

MIN_DURATION = 10
MAX_DURATION = 120


def api_request(endpoint, params=None):
    """Make a request to the Freesound API."""
    params = params or {}
    params["token"] = FREESOUND_API_KEY
    params["format"] = "json"

    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LittleStarFactory/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"    API error: {e}")
        return None


def search_sounds(query, limit=5):
    """Search for CC0 music tracks on Freesound."""
    data = api_request("search/text/", {
        "query": query,
        "filter": f"license:\"Creative Commons 0\" duration:[{MIN_DURATION} TO {MAX_DURATION}]",
        "fields": "id,name,duration,previews,license,avg_rating,num_ratings,tags",
        "sort": "rating_desc",
        "page_size": limit,
    })

    if not data:
        return []

    return data.get("results", [])


def download_sound(sound, dest_dir):
    """Download a sound's preview (MP3, good quality, no auth needed)."""
    previews = sound.get("previews", {})
    url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")

    if not url:
        print(f"    No preview URL for: {sound.get('name', 'unknown')}")
        return False

    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in sound["name"])
    safe_name = safe_name.strip()[:80]
    filename = f"{sound['id']}_{safe_name}.mp3"
    filepath = os.path.join(dest_dir, filename)

    if os.path.exists(filepath):
        print(f"    Already exists: {filename}")
        return True

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LittleStarFactory/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())

        size_kb = os.path.getsize(filepath) / 1024
        duration = sound.get("duration", 0)
        print(f"    Saved: {filename} ({duration:.0f}s, {size_kb:.0f}KB)")
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def download_mood(mood, terms, limit=5):
    """Download tracks for a single mood category."""
    mood_dir = os.path.join(MUSIC_DIR, mood)
    os.makedirs(mood_dir, exist_ok=True)

    total = 0
    seen_ids = set()

    existing = [f for f in os.listdir(mood_dir) if f.endswith((".mp3", ".wav", ".m4a", ".ogg"))]
    print(f"  Existing tracks: {len(existing)}")

    for term in terms:
        print(f"\n  Searching: \"{term}\"")
        results = search_sounds(term, limit=limit)

        if not results:
            print(f"    No results")
            continue

        for sound in results:
            if sound["id"] in seen_ids:
                continue
            seen_ids.add(sound["id"])

            if download_sound(sound, mood_dir):
                total += 1

        time.sleep(0.5)

    return total


def main():
    parser = argparse.ArgumentParser(description="Download free music from Freesound.org")
    parser.add_argument("--mood", type=str, choices=list(SEARCH_TERMS.keys()),
                        help="Download only this mood")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max tracks per search term (default: 5)")
    parser.add_argument("--list", action="store_true",
                        help="List available moods and search terms")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable moods:")
        for mood, terms in SEARCH_TERMS.items():
            print(f"\n  [{mood}] — {len(terms)} search terms")
            for t in terms:
                print(f"    - {t}")
        print(f"\n  Duration filter: {MIN_DURATION}-{MAX_DURATION} seconds")
        print(f"  License: Creative Commons 0 (free, no attribution)")
        return

    if not FREESOUND_API_KEY:
        print("ERROR: FREESOUND_API_KEY not set.\n")
        print("Setup steps:")
        print("  1. Create free account: https://freesound.org/home/register/")
        print("  2. Get API key: https://freesound.org/apiv2/apply/")
        print("     (choose 'APIv2 credential', any description works)")
        print("  3. Add to kids_poems/.env:")
        print("     FREESOUND_API_KEY=your_key_here")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Music Downloader — LittleStarFactory")
    print("  Source: Freesound.org (CC0 — free commercial use)")
    print("=" * 55)

    moods = {args.mood: SEARCH_TERMS[args.mood]} if args.mood else SEARCH_TERMS
    grand_total = 0

    for mood, terms in moods.items():
        print(f"\n{'─' * 55}")
        print(f"  [{mood}] — {len(terms)} search terms, limit {args.limit} each")
        print(f"{'─' * 55}")
        count = download_mood(mood, terms, limit=args.limit)
        grand_total += count

    print(f"\n{'=' * 55}")
    print(f"  Done! Total tracks downloaded: {grand_total}")
    print(f"  Saved to: {MUSIC_DIR}")
    print(f"  License: CC0 — free for commercial use, no attribution needed")
    print(f"\n  Folder structure:")
    for mood in moods:
        mood_dir = os.path.join(MUSIC_DIR, mood)
        if os.path.isdir(mood_dir):
            count = len([f for f in os.listdir(mood_dir)
                        if f.endswith((".mp3", ".wav", ".m4a", ".ogg"))])
            print(f"    music/{mood}/ — {count} tracks")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
