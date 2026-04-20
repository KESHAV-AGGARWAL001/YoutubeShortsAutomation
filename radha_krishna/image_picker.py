import os
import random
from config import IMAGE_FOLDER, IMAGES_PER_VIDEO, SUPPORTED_IMAGE_FORMATS


def get_all_images():
    if not os.path.isdir(IMAGE_FOLDER):
        raise FileNotFoundError(f"Image folder not found: {IMAGE_FOLDER}")

    images = [
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(SUPPORTED_IMAGE_FORMATS)
    ]

    if not images:
        raise FileNotFoundError(f"No images found in {IMAGE_FOLDER}")

    return images


def pick_random_images(count=None):
    count = count or IMAGES_PER_VIDEO
    images = get_all_images()

    if len(images) < count:
        print(f"  Only {len(images)} images available, using all of them")
        selected = images[:]
        random.shuffle(selected)
    else:
        selected = random.sample(images, count)

    print(f"  Selected {len(selected)} images for slideshow")
    return selected


if __name__ == "__main__":
    for img in pick_random_images():
        print(f"  - {os.path.basename(img)}")
