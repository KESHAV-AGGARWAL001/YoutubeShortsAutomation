"""
download_pixabay.py — Pixabay API Image Downloader for Kids Poems

Downloads free, copyright-safe kids illustrations from Pixabay.
All Pixabay images are licensed under their Content License (free for commercial use).

Prerequisites:
  1. Create a free account at https://pixabay.com/accounts/register/
  2. Get your API key from https://pixabay.com/api/docs/
  3. Set PIXABAY_API_KEY in kids_poems/.env

Usage:
  python download_pixabay.py                     # Download all categories
  python download_pixabay.py --category animal   # Download one category
  python download_pixabay.py --limit 15          # Limit per search term
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "assets", "images")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

SEARCH_TERMS = {
    "general": [
        "kids cartoon illustration",
        "children book illustration",
        "cute cartoon character",
        "colorful kids art",
        "preschool cartoon",
    ],
    "animal": [
        "cute cartoon animal",
        "cartoon bunny kids",
        "cartoon duck illustration",
        "cartoon farm animals",
        "cartoon dinosaur kids",
        "cartoon cat cute",
        "baby elephant cartoon",
    ],
    "nursery_rhyme": [
        "nursery rhyme illustration",
        "twinkle star cartoon",
        "fairy tale kids illustration",
        "storybook cartoon",
        "mother goose illustration",
    ],
    "counting": [
        "cartoon numbers kids",
        "counting kids illustration",
        "numbers preschool colorful",
        "math kids cartoon",
    ],
    "alphabet": [
        "ABC kids cartoon",
        "alphabet illustration children",
        "letter cartoon colorful",
        "alphabet animal kids",
    ],
    "colors": [
        "rainbow cartoon kids",
        "colorful shapes children",
        "rainbow illustration bright",
        "colors kids learning",
    ],
    "bedtime": [
        "moon stars kids cartoon",
        "bedtime illustration children",
        "night sky cartoon cute",
        "sleeping cartoon kids",
        "lullaby illustration",
    ],
    "seasonal": [
        "christmas cartoon kids",
        "halloween cute cartoon",
        "spring cartoon children",
        "snowflake cartoon kids",
        "easter bunny cartoon",
    ],
    "action": [
        "kids playing cartoon",
        "dancing cartoon children",
        "jumping kids illustration",
        "happy kids cartoon",
        "funny cartoon children",
    ],
}


def search_pixabay(query, limit=10):
    """Search Pixabay API and return image URLs."""
    params = urllib.parse.urlencode({
        "key": PIXABAY_API_KEY,
        "q": query,
        "image_type": "illustration",
        "category": "education",
        "safesearch": "true",
        "per_page": min(limit, 200),
        "order": "popular",
    })

    url = f"https://pixabay.com/api/?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LittleStarFactory/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("hits", [])
    except Exception as e:
        print(f"    API error: {e}")
        return []


def download_image(url, filepath):
    """Download a single image."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LittleStarFactory/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(filepath, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


def download_category(category, terms, limit=10):
    """Download images for a single category from Pixabay."""
    cat_dir = os.path.join(DOWNLOAD_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)

    existing = set(os.listdir(cat_dir))
    total = 0
    img_index = len(existing)

    for term in terms:
        print(f"  Searching: {term}")
        hits = search_pixabay(term, limit=limit)

        if not hits:
            print(f"    No results")
            continue

        downloaded = 0
        for hit in hits:
            img_url = hit.get("webformatURL", "")
            if not img_url:
                continue

            ext = img_url.rsplit(".", 1)[-1].split("?")[0]
            if ext not in ("jpg", "jpeg", "png", "webp"):
                ext = "jpg"

            filename = f"{category}_{img_index:04d}.{ext}"
            filepath = os.path.join(cat_dir, filename)

            if download_image(img_url, filepath):
                downloaded += 1
                img_index += 1
                total += 1

        print(f"    Downloaded: {downloaded} images")
        time.sleep(0.5)

    return total


def main():
    parser = argparse.ArgumentParser(description="Download kids illustrations from Pixabay")
    parser.add_argument("--category", type=str, help="Download only this category")
    parser.add_argument("--limit", type=int, default=10, help="Max images per search term (default: 10)")
    parser.add_argument("--list", action="store_true", help="List available categories")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable categories:")
        for cat, terms in SEARCH_TERMS.items():
            print(f"  {cat} ({len(terms)} search terms)")
        return

    if not PIXABAY_API_KEY:
        print("ERROR: PIXABAY_API_KEY not set.")
        print("\nSetup steps:")
        print("  1. Create free account: https://pixabay.com/accounts/register/")
        print("  2. Get API key: https://pixabay.com/api/docs/")
        print("  3. Add to kids_poems/.env: PIXABAY_API_KEY=your_key_here")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Pixabay Image Downloader — LittleStarFactory")
    print("=" * 55)

    categories = {args.category: SEARCH_TERMS[args.category]} if args.category else SEARCH_TERMS
    grand_total = 0

    for cat, terms in categories.items():
        print(f"\n[{cat}] — {len(terms)} search terms, limit {args.limit} each")
        count = download_category(cat, terms, limit=args.limit)
        grand_total += count

    print(f"\n{'=' * 55}")
    print(f"  Done! Total images downloaded: {grand_total}")
    print(f"  Saved to: {DOWNLOAD_DIR}")
    print(f"  License: Pixabay Content License (free for commercial use)")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
