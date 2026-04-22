"""
download_pinterest.py — Pinterest Image Scraper for Kids Poems

Downloads kids cartoon illustrations from Pinterest using gallery-dl.
Organizes images into category folders matching the pipeline structure.

Prerequisites:
  pip install gallery-dl

Usage:
  python download_pinterest.py                  # Download all categories
  python download_pinterest.py --category animal  # Download one category
  python download_pinterest.py --limit 20        # Limit per search term
"""

import os
import sys
import subprocess
import argparse
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "assets", "images")

SEARCH_TERMS = {
    "general": [
        "kids cartoon illustration",
        "children's book illustration art",
        "cute cartoon characters for kids",
        "toddler friendly cartoon art",
        "bright colorful kids illustration",
        "2D flat illustration for children",
    ],
    "animal": [
        "cute cartoon animals for kids",
        "baby animal illustration kawaii",
        "cartoon duck pond kids",
        "cute cartoon bunny illustration",
        "friendly cartoon farm animals",
        "cartoon jungle animals for toddlers",
        "cartoon ocean animals kids",
        "cute cartoon dinosaur kids",
    ],
    "nursery_rhyme": [
        "nursery rhyme illustration art",
        "twinkle twinkle little star cartoon",
        "humpty dumpty kids illustration",
        "mother goose cartoon art",
        "kids poem visual illustration",
        "storybook nursery rhyme art",
    ],
    "counting": [
        "cartoon numbers for kids",
        "counting illustration preschool",
        "number characters cartoon kids",
        "colorful numbers cartoon toddler",
        "123 kids learning illustration",
    ],
    "alphabet": [
        "ABC cartoon illustration kids",
        "alphabet characters for children",
        "letter learning cartoon art",
        "cute alphabet animal illustration",
        "preschool letter cartoon art",
    ],
    "colors": [
        "rainbow cartoon kids illustration",
        "learn colors kids cartoon",
        "colorful shapes for toddlers art",
        "primary colors cartoon illustration",
        "shapes cartoon preschool art",
    ],
    "bedtime": [
        "bedtime cartoon illustration kids",
        "sleepy moon stars cartoon",
        "goodnight kids illustration art",
        "dreamy night sky cartoon toddler",
        "lullaby illustration soft pastel",
    ],
    "seasonal": [
        "christmas cartoon kids illustration",
        "halloween cute cartoon for kids",
        "spring flowers cartoon children",
        "winter snowflake cartoon kids",
        "easter bunny kids cartoon art",
    ],
    "action": [
        "kids dancing cartoon illustration",
        "clapping hands cartoon kids",
        "jumping cartoon toddler art",
        "funny cartoon kids laughing",
        "silly face cartoon for children",
    ],
}


def check_gallery_dl():
    """Check if gallery-dl is installed."""
    if shutil.which("gallery-dl"):
        return True
    try:
        subprocess.run(
            [sys.executable, "-m", "gallery_dl", "--version"],
            capture_output=True, text=True,
        )
        return True
    except Exception:
        return False


def download_category(category, terms, limit=10):
    """Download images for a single category from Pinterest."""
    cat_dir = os.path.join(DOWNLOAD_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)

    total = 0
    for term in terms:
        search_url = f"https://www.pinterest.com/search/pins/?q={term.replace(' ', '%20')}"
        print(f"  Searching: {term}")

        cmd = [
            "gallery-dl",
            "--dest", cat_dir,
            "--range", f"1-{limit}",
            "--filename", "{category}_{num:>03}.{extension}",
            search_url,
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                count = result.stdout.count("\n") if result.stdout else 0
                total += count
                print(f"    Downloaded: {count} images")
            else:
                print(f"    Warning: {result.stderr[:200] if result.stderr else 'No output'}")
        except subprocess.TimeoutExpired:
            print(f"    Timeout — skipping")
        except Exception as e:
            print(f"    Error: {e}")

    return total


def main():
    parser = argparse.ArgumentParser(description="Download kids cartoon images from Pinterest")
    parser.add_argument("--category", type=str, help="Download only this category")
    parser.add_argument("--limit", type=int, default=10, help="Max images per search term (default: 10)")
    parser.add_argument("--list", action="store_true", help="List available categories")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable categories:")
        for cat, terms in SEARCH_TERMS.items():
            print(f"  {cat} ({len(terms)} search terms)")
        return

    if not check_gallery_dl():
        print("ERROR: gallery-dl is not installed.")
        print("Install it with: pip install gallery-dl")
        print("Then run this script again.")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Pinterest Image Downloader — LittleStarFactory")
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
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
