"""
flatten_images.py — Move Subfolder Images Into assets/images/

Moves all images from subfolders inside assets/images/ up to the root.
Example: assets/images/animal/duck.png → assets/images/animal_duck.png

Usage:
  python flatten_images.py              # Flatten all subfolders
  python flatten_images.py --dry-run    # Preview without making changes
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

    for root, dirs, files in os.walk(IMAGES_DIR, topdown=False):
        if os.path.abspath(root) == os.path.abspath(IMAGES_DIR):
            continue

        folder_name = os.path.relpath(root, IMAGES_DIR).replace(os.sep, "_")
        image_files = [f for f in files if f.lower().endswith(SUPPORTED)]

        if not image_files:
            continue

        print(f"  [{folder_name}] — {len(image_files)} images")

        for filename in image_files:
            src = os.path.join(root, filename)

            if filename.startswith(f"{folder_name}_"):
                new_name = filename
            else:
                new_name = f"{folder_name}_{filename}"

            dest = os.path.join(IMAGES_DIR, new_name)

            if os.path.exists(dest):
                name, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(dest):
                    dest = os.path.join(IMAGES_DIR, f"{name}_{counter}{ext}")
                    counter += 1

            if dry_run:
                print(f"    [DRY RUN] → {os.path.basename(dest)}")
            else:
                shutil.move(src, dest)

            moved += 1

        if not dry_run and not os.listdir(root):
            os.rmdir(root)
            print(f"    Removed empty folder: {folder_name}/")

    print(f"\n  {'[DRY RUN] ' if dry_run else ''}Moved: {moved} images to assets/images/")


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
