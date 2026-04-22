"""
flatten_images.py — Move All Images Into assets/images/

Scans the entire kids_poems/ folder (and all subfolders) for images,
then moves them all into assets/images/ as a flat list.
Skips assets/output/ (pipeline working directory).

Usage:
  python flatten_images.py                          # Scan kids_poems/ and flatten
  python flatten_images.py --source "C:/Downloads"  # Scan a custom folder instead
  python flatten_images.py --dry-run                # Preview without making changes
"""

import os
import sys
import shutil
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(BASE_DIR, "assets", "images")
SUPPORTED = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

SKIP_FOLDERS = {"assets/output", "__pycache__", ".git", "archive"}


def find_all_images(source_dir):
    """Recursively find all image files, skipping output/cache folders."""
    images = []
    dest_abs = os.path.abspath(DEST_DIR)

    for root, dirs, files in os.walk(source_dir):
        root_abs = os.path.abspath(root)

        if root_abs == dest_abs:
            dirs.clear()
            continue

        skip = False
        for s in SKIP_FOLDERS:
            if s in root_abs.replace("\\", "/"):
                skip = True
                break
        if skip:
            continue

        for f in files:
            if f.lower().endswith(SUPPORTED):
                images.append(os.path.join(root, f))

    return images


def flatten(source_dir, dry_run=False):
    os.makedirs(DEST_DIR, exist_ok=True)

    images = find_all_images(source_dir)

    if not images:
        print(f"  No images found in: {source_dir}")
        print(f"  Supported formats: {', '.join(SUPPORTED)}")
        return

    print(f"  Found {len(images)} images in: {source_dir}\n")

    moved = 0
    skipped = 0

    for src in images:
        src_abs = os.path.abspath(src)
        dest_abs = os.path.abspath(DEST_DIR)

        if os.path.dirname(src_abs) == dest_abs:
            skipped += 1
            continue

        filename = os.path.basename(src)
        parent = os.path.basename(os.path.dirname(src))

        if parent.lower() not in ("images", "kids_poems", os.path.basename(source_dir).lower()):
            if not filename.startswith(f"{parent}_"):
                filename = f"{parent}_{filename}"

        dest = os.path.join(DEST_DIR, filename)

        if os.path.exists(dest):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(DEST_DIR, f"{name}_{counter}{ext}")
                counter += 1

        if dry_run:
            print(f"  [DRY RUN] {src} → {os.path.basename(dest)}")
        else:
            shutil.move(src, dest)
            print(f"  Moved: {os.path.basename(dest)}")

        moved += 1

    if not dry_run:
        cleaned = 0
        for root, dirs, files in os.walk(source_dir, topdown=False):
            root_abs = os.path.abspath(root)
            if root_abs == os.path.abspath(source_dir):
                continue
            if root_abs.startswith(os.path.abspath(DEST_DIR)):
                continue
            if not os.listdir(root_abs):
                try:
                    os.rmdir(root_abs)
                    cleaned += 1
                except OSError:
                    pass
        if cleaned:
            print(f"\n  Cleaned up {cleaned} empty folders")

    print(f"\n  {'[DRY RUN] ' if dry_run else ''}Total moved: {moved}")
    if skipped:
        print(f"  Already in destination: {skipped}")
    print(f"  Destination: {DEST_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Flatten all images into assets/images/")
    parser.add_argument("--source", type=str, help="Source folder to scan (default: kids_poems/)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    source = args.source or BASE_DIR

    print("\n" + "=" * 55)
    print("  Flatten Images — LittleStarFactory")
    print("=" * 55 + "\n")

    flatten(source, dry_run=args.dry_run)

    print(f"\n{'=' * 55}")


if __name__ == "__main__":
    main()
