"""
image_generator.py — AI Image Generator for Kids Poems

Generates one colorful illustration per poem line using Gemini's
image generation capabilities. Falls back to picking from a
pre-existing image folder if generation fails.
"""

import os
import sys
import json
import base64
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    GEMINI_IMAGE_MODEL, IMAGE_FOLDER, OUTPUT_FOLDER,
    SUPPORTED_IMAGE_FORMATS,
)

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_image(visual_description, output_path, index=0):
    """Generate a single image from a visual description using Gemini."""
    prompt = (
        f"Create a children's book illustration: {visual_description}. "
        f"Style: cute cartoon, bright vivid colors, simple shapes, "
        f"child-friendly, happy mood, no text or words in the image, "
        f"high quality digital art, 2D illustration."
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img_data = part.inline_data.data
                if isinstance(img_data, str):
                    img_data = base64.b64decode(img_data)
                with open(output_path, "wb") as f:
                    f.write(img_data)
                size_kb = os.path.getsize(output_path) / 1024
                print(f"    Image {index + 1}: {size_kb:.0f}KB — {output_path}")
                return True

        print(f"    Image {index + 1}: No image in response")
        return False

    except Exception as e:
        print(f"    Image {index + 1}: Generation failed — {e}")
        return False


def generate_all_images(poem_data):
    """
    Generate images for all poem lines.
    Falls back to pre-existing images from assets/images/ if AI generation fails.
    """
    visuals = poem_data.get("visual_descriptions", [])
    poem_lines = poem_data.get("poem_lines", [])
    images_dir = os.path.join(OUTPUT_FOLDER, "images")
    os.makedirs(images_dir, exist_ok=True)

    generated_paths = []
    failed_indices = []

    print(f"  Generating {len(visuals)} images...")

    for i, desc in enumerate(visuals):
        img_path = os.path.join(images_dir, f"scene_{i:02d}.png")
        if generate_image(desc, img_path, i):
            generated_paths.append(img_path)
        else:
            failed_indices.append(i)

    # Fill failed slots from pre-existing images folder
    if failed_indices:
        fallback_images = _get_fallback_images()
        if fallback_images:
            print(f"  Filling {len(failed_indices)} failed slots from assets/images/")
            for i in failed_indices:
                img_path = os.path.join(images_dir, f"scene_{i:02d}.png")
                fb = random.choice(fallback_images)
                import shutil
                shutil.copy2(fb, img_path)
                generated_paths.insert(i, img_path)
                print(f"    Image {i + 1}: fallback — {os.path.basename(fb)}")
        else:
            print(f"  WARNING: {len(failed_indices)} images failed, no fallback available")

    # Sort by filename to maintain order
    generated_paths.sort()
    print(f"  Total images: {len(generated_paths)}")
    return generated_paths


def _get_fallback_images():
    """Get list of pre-existing images from assets/images/ folder."""
    if not os.path.isdir(IMAGE_FOLDER):
        return []
    return [
        os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith(SUPPORTED_IMAGE_FORMATS)
    ]


def main():
    print("=" * 50)
    print("  Kids Poem Image Generator")
    print("=" * 50)

    poem_file = os.path.join(OUTPUT_FOLDER, "poem_data.json")
    if not os.path.exists(poem_file):
        print("  ERROR: Run poem_generator.py first")
        return

    with open(poem_file, "r", encoding="utf-8") as f:
        poem_data = json.load(f)

    print(f"\n  Poem: {poem_data.get('poem_title', 'Unknown')}")
    images = generate_all_images(poem_data)

    print(f"\n  Generated {len(images)} images")
    print("=" * 50)


if __name__ == "__main__":
    main()
