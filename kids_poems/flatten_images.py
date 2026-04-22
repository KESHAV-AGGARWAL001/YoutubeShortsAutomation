"""
flatten_images.py — Move All Images Into a Single Folder

Moves all images from category subfolders into assets/images/ root.
Renames files to avoid conflicts: {category}_{original_name}.ext

Usage:
  python flatten_images.py              # Flatten all subfolders
  python flatten_images.py --dry-run    # Preview what will happen (no changes)
"""

import os
import sys
import shutil
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
SUPPORTED = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")


def flatten(dry_run=False):
    if not os.path.isdir(IMAGES_DIR):
        print(f"  ERROR: {IMAGES_DIR} does not exist")
        return

    moved = 0
    skipped = 0

    for folder in sorted(os.listdir(IMAGES_DIR)):
        folder_path = os.path.join(IMAGES_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
            and f.lower().endswith(SUPPORTED)
        ]

        if not files:
            continue

        print(f"  [{folder}] — {len(files)} images")

        for filename in files:
            src = os.path.join(folder_path, filename)

            if filename.startswith(f"{folder}_"):
                new_name = filename
            else:
                new_name = f"{folder}_{filename}"

            dest = os.path.join(IMAGES_DIR, new_name)

            if os.path.exists(dest):
                name, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(dest):
                    dest = os.path.join(IMAGES_DIR, f"{name}_{counter}{ext}")
                    counter += 1

            if dry_run:
                print(f"    [DRY RUN] {src} → {os.path.basename(dest)}")
            else:
                shutil.move(src, dest)

            moved += 1

        if not dry_run:
            remaining = os.listdir(folder_path)
            if not remaining:
                os.rmdir(folder_path)
                print(f"    Removed empty folder: {folder}/")
            else:
                skipped += len(remaining)
                print(f"    Kept folder (has {len(remaining)} non-image files)")

    print(f"\n  {'[DRY RUN] ' if dry_run else ''}Moved: {moved} images to assets/images/")
    if skipped:
        print(f"  Skipped: {skipped} non-image files left in subfolders")


def main():
    parser = argparse.ArgumentParser(description="Flatten image subfolders into assets/images/")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  Flatten Images — LittleStarFactory")
    print("=" * 55 + "\n")

    flatten(dry_run=args.dry_run)

    print(f"\n{'=' * 55}")


if __name__ == "__main__":
    main()
