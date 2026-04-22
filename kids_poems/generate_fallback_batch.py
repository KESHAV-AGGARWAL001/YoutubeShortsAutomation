"""
generate_fallback_batch.py — Gemini Batch Image Generator for Kids Poems

Generates fallback images using your own Gemini API key.
These match the exact style your pipeline uses — perfect consistency.
100% copyright-free (you own the generated images).

Prerequisites:
  Set KP_GEMINI_API_KEY in kids_poems/.env

Usage:
  python generate_fallback_batch.py                     # Generate all categories
  python generate_fallback_batch.py --category animal   # One category only
  python generate_fallback_batch.py --count 8           # Images per prompt
"""

import os
import sys
import time
import base64
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL

from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "assets", "images")

STYLE_SUFFIX = (
    "Cute cartoon style, bright vivid colors, simple shapes, "
    "child-friendly, happy mood, no text, no words, "
    "high quality digital art, 2D children's book illustration, "
    "colorful background, safe for toddlers."
)

PROMPTS = {
    "general": [
        "A cheerful cartoon sun smiling in a bright blue sky with fluffy white clouds",
        "A magical rainbow arching over green hills with tiny flowers",
        "A colorful cartoon playground with slides and swings",
        "A happy cartoon train chugging through a countryside",
        "A cute cartoon treehouse with a ladder and colorful flags",
        "A bright cartoon garden with smiling flowers and butterflies",
        "A cartoon candy land with lollipops and gummy bears",
        "A cheerful cartoon hot air balloon floating over mountains",
    ],
    "animal": [
        "A cute cartoon bunny hopping in a green meadow with daisies",
        "A friendly cartoon duck family swimming in a pond",
        "A happy cartoon kitten playing with a ball of yarn",
        "A silly cartoon monkey hanging from a tree branch",
        "A gentle cartoon elephant spraying water with its trunk",
        "A colorful cartoon parrot sitting on a tropical branch",
        "A cute cartoon puppy with floppy ears running in a park",
        "A friendly cartoon frog sitting on a lily pad",
        "A cartoon baby penguin sliding on ice",
        "A cute cartoon ladybug on a big green leaf",
    ],
    "nursery_rhyme": [
        "A twinkling cartoon star in a dark blue night sky with a crescent moon",
        "Humpty Dumpty sitting happily on a colorful brick wall",
        "A cartoon dish running away with a spoon under moonlight",
        "Little Bo Peep looking for cartoon sheep on a green hill",
        "Jack and Jill cartoon characters climbing a hill with a pail",
        "A cartoon itsy bitsy spider climbing a water spout in rain",
        "Three blind cartoon mice running with sunglasses",
        "A cartoon Mary with a little white lamb at school",
    ],
    "counting": [
        "The number 1 as a cartoon character wearing a crown",
        "Five colorful cartoon fingers on a hand waving hello",
        "Ten cartoon apples arranged in two rows on a table",
        "Three cartoon bears of different sizes standing together",
        "Seven cartoon stars arranged in a circle in the night sky",
        "Two cartoon shoes — one red and one blue — side by side",
        "Four cartoon seasons shown as quadrants — spring summer autumn winter",
        "Six cartoon balloons floating upward in different colors",
    ],
    "alphabet": [
        "The letter A as a cartoon character holding a red apple",
        "The letter B as a cartoon character with butterfly wings",
        "The letter C as a cartoon character shaped like a cat",
        "A cartoon alphabet train with ABC on each car",
        "The letter D as a cartoon character playing drums",
        "The letter Z as a cartoon character dressed as a zebra",
        "All 26 cartoon letters dancing in a circle on green grass",
        "The letter S as a cartoon character shaped like a snake",
    ],
    "colors": [
        "A bright red cartoon fire truck on a city street",
        "An orange cartoon sunset over a cartoon ocean",
        "A yellow cartoon sun wearing sunglasses",
        "A green cartoon frog prince wearing a tiny crown",
        "A blue cartoon whale swimming in a happy ocean",
        "A purple cartoon butterfly with sparkling wings",
        "A pink cartoon flamingo standing on one leg",
        "A cartoon rainbow with each color band glowing brightly",
    ],
    "bedtime": [
        "A cartoon crescent moon wearing a nightcap with stars around",
        "A cute cartoon baby bear sleeping in a cozy bed with a blanket",
        "A peaceful cartoon night sky with twinkling stars and fireflies",
        "A cartoon owl sitting on a tree branch at night with half-closed eyes",
        "A cozy cartoon bedroom with a nightlight and stuffed animals",
        "A cartoon cloud shaped like a pillow floating in a starry sky",
        "A sleepy cartoon bunny yawning in pajamas",
        "A cartoon music box with musical notes floating around it",
    ],
    "seasonal": [
        "A cartoon snowman wearing a scarf in a winter wonderland",
        "Cartoon cherry blossoms blooming in a spring garden",
        "A cartoon beach scene with sandcastle and smiling sun",
        "Cartoon autumn leaves falling from a tree in orange and gold",
        "A cartoon pumpkin patch with friendly jack-o-lanterns",
        "A cartoon Christmas tree with colorful ornaments and a star on top",
        "Cartoon Easter eggs hidden in colorful grass",
        "A cartoon Valentine heart with a cute face",
    ],
    "action": [
        "Cartoon kids clapping their hands in a circle",
        "A cartoon toddler jumping up with arms raised high",
        "Cartoon children dancing in a circle holding hands",
        "A cartoon kid doing a funny silly face with tongue out",
        "Cartoon kids stomping their feet on a wooden floor",
        "A cartoon child spinning around with a dizzy face",
        "Cartoon kids waving their hands in the air",
        "A cartoon child blowing bubbles in a garden",
    ],
}


def generate_image(prompt, output_path, retries=3):
    """Generate a single image using Gemini."""
    full_prompt = f"Create a children's book illustration: {prompt}. {STYLE_SUFFIX}"

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            if not response.candidates:
                print(f"    No candidates returned (attempt {attempt + 1})")
                time.sleep(3)
                continue

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_data = part.inline_data.data
                    if isinstance(img_data, str):
                        img_data = base64.b64decode(img_data)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    return True

            print(f"    No image in response (attempt {attempt + 1})")
            time.sleep(3)

        except Exception as e:
            print(f"    Error (attempt {attempt + 1}): {e}")
            wait = 5 * (attempt + 1)
            time.sleep(wait)

    return False


def generate_category(category, prompts, count=None):
    """Generate images for a single category."""
    cat_dir = os.path.join(DOWNLOAD_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)

    existing = len([f for f in os.listdir(cat_dir) if f.endswith((".png", ".jpg"))])
    prompts_to_use = prompts[:count] if count else prompts
    total = 0

    for i, prompt in enumerate(prompts_to_use):
        idx = existing + i
        filename = f"{category}_gen_{idx:04d}.png"
        filepath = os.path.join(cat_dir, filename)

        short_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt
        print(f"  [{i + 1}/{len(prompts_to_use)}] {short_prompt}")

        if generate_image(prompt, filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"    Saved: {filename} ({size_kb:.0f}KB)")
            total += 1
        else:
            print(f"    FAILED — skipping")

        time.sleep(2)

    return total


def main():
    parser = argparse.ArgumentParser(description="Generate fallback images with Gemini AI")
    parser.add_argument("--category", type=str, help="Generate only this category")
    parser.add_argument("--count", type=int, help="Max images per category (default: all prompts)")
    parser.add_argument("--list", action="store_true", help="List available categories")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable categories:")
        for cat, prompts in PROMPTS.items():
            print(f"  {cat} ({len(prompts)} prompts)")
        total = sum(len(p) for p in PROMPTS.values())
        print(f"\n  Total: {total} images across all categories")
        return

    if not GEMINI_API_KEY:
        print("ERROR: KP_GEMINI_API_KEY not set.")
        print("Add it to kids_poems/.env")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Gemini Batch Image Generator — LittleStarFactory")
    print(f"  Model: {GEMINI_IMAGE_MODEL}")
    print("=" * 55)

    categories = {args.category: PROMPTS[args.category]} if args.category else PROMPTS
    grand_total = 0

    for cat, prompts in categories.items():
        count = args.count or len(prompts)
        print(f"\n[{cat}] — generating {min(count, len(prompts))} images")
        result = generate_category(cat, prompts, count=count)
        grand_total += result

    print(f"\n{'=' * 55}")
    print(f"  Done! Total images generated: {grand_total}")
    print(f"  Saved to: {DOWNLOAD_DIR}")
    print(f"  License: You own these (AI-generated, copyright-free)")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
