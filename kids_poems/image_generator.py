"""
image_generator.py — AI Image Generator for Kids Poems

Generates one colorful illustration per poem line.
Fallback chain: Gemini (Nano Banana) → Pollinations.ai (free) → local assets/images/
"""

import os
import sys
import json
import base64
import random
import time
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    GEMINI_API_KEY, GEMINI_IMAGE_MODEL, IMAGE_FOLDER, OUTPUT_FOLDER,
    SUPPORTED_IMAGE_FORMATS,
)

from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

_gemini_failed = False


def _generate_image_pollinations(prompt, output_path, index=0):
    """Generate image using Pollinations.ai — free, no API key needed."""
    encoded_prompt = urllib.parse.quote(prompt, safe="")
    url = (
        f"https://gen.pollinations.ai/image/{encoded_prompt}"
        f"?width=1080&height=1920&nologo=true&model=flux"
    )

    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(5 * attempt)

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(output_path, "wb") as f:
                        f.write(data)
                    size_kb = len(data) / 1024
                    print(f"    Image {index + 1} (Pollinations): {size_kb:.0f}KB")
                    return True
                print(f"    Image {index + 1}: Pollinations returned empty response")

        except Exception as e:
            if attempt < 2:
                continue
            print(f"    Pollinations failed: {e}")

    return False


def generate_image(visual_description, output_path, index=0):
    """Generate a single image. Tries Gemini first, then Pollinations.ai."""
    global _gemini_failed

    prompt = (
        f"Create a children's book illustration: {visual_description}. "
        f"Style: cute cartoon, bright vivid colors, simple shapes, "
        f"child-friendly, happy mood, no text or words in the image, "
        f"high quality digital art, 2D illustration."
    )

    if client and not _gemini_failed:
        for attempt in range(2):
            try:
                if attempt > 0:
                    time.sleep(10)

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
                        print(f"    Image {index + 1}: {size_kb:.0f}KB")
                        return True

                print(f"    Image {index + 1}: No image in Gemini response")
                break

            except Exception as e:
                err = str(e).lower()
                if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate"]):
                    if attempt == 0:
                        print(f"    Gemini rate-limited — retrying in 10s...")
                        continue
                    print(f"    Gemini overloaded — switching to Pollinations for remaining images...")
                    _gemini_failed = True
                else:
                    print(f"    Gemini failed: {e}")
                    break

    return _generate_image_pollinations(prompt, output_path, index)


def generate_all_images(poem_data):
    """
    Generate images for all poem lines.
    Falls back to pre-existing images from assets/images/ if AI generation fails.
    """
    visuals = poem_data.get("visual_descriptions", [])
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

    generated_paths.sort()
    print(f"  Total images: {len(generated_paths)}")
    return generated_paths


def generate_fallback_images(poem_data, indices):
    """
    Generate images only for specific verse indices (used when Veo fails
    for certain verses). Returns dict mapping index to image path.
    """
    visuals = poem_data.get("visual_descriptions", [])
    images_dir = os.path.join(OUTPUT_FOLDER, "images")
    os.makedirs(images_dir, exist_ok=True)

    result = {}
    fallbacks = _get_fallback_images()

    for i in indices:
        img_path = os.path.join(images_dir, f"fallback_{i:02d}.png")
        desc = visuals[i] if i < len(visuals) else "colorful cartoon scene for children"

        if generate_image(desc, img_path, i):
            result[i] = img_path
        elif fallbacks:
            import shutil
            fb = random.choice(fallbacks)
            shutil.copy2(fb, img_path)
            result[i] = img_path
            print(f"    Fallback {i + 1}: {os.path.basename(fb)}")

    return result


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
