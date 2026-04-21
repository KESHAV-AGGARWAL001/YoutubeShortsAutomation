"""
poem_generator.py — AI Poem + SEO Generator for Kids Channel

Uses Gemini to generate original children's poems with:
  - Age-appropriate language (2-6 years)
  - Rhyming structure
  - Per-verse visual descriptions (for image generation)
  - YouTube SEO (title, description, tags)
"""

import os
import sys
import json
import random
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    GEMINI_MODEL, POEM_CATEGORIES, OUTPUT_FOLDER,
    POEMS_FOLDER, DEFAULT_TAGS, CHANNEL_NAME,
)

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
FALLBACK_MODEL = "gemini-2.0-flash"


def ask_gemini(prompt, model=None):
    model = model or GEMINI_MODEL
    for attempt in range(4):
        use_model = model if attempt < 3 else FALLBACK_MODEL
        try:
            if attempt > 0:
                wait = min(2 ** attempt * 5, 60)
                print(f"  Retry {attempt}/3 — waiting {wait}s... (model: {use_model})")
                time.sleep(wait)
            response = client.models.generate_content(
                model=use_model, contents=prompt
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return text
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate"]):
                if attempt < 3:
                    continue
            raise


def sanitize_json(text):
    result = []
    in_str = False
    for i, ch in enumerate(text):
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_str = not in_str
            result.append(ch)
        elif in_str:
            if ch == '\n':
                result.append('\\n')
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            elif ord(ch) < 0x20:
                pass
            else:
                result.append(ch)
        else:
            result.append(ch)
    return ''.join(result)


def parse_json_safe(text, retries=2, prompt=None):
    text = sanitize_json(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = text.rstrip()
        open_b = repaired.count('{') - repaired.count('}')
        open_s = repaired.count('[') - repaired.count(']')
        if open_s > 0:
            repaired += ']' * open_s
        if open_b > 0:
            repaired += '}' * open_b
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            if retries > 0 and prompt:
                print(f"  Retrying JSON parse... ({retries} left)")
                new_text = ask_gemini(prompt)
                return parse_json_safe(new_text, retries - 1, prompt)
            raise ValueError(f"Failed to parse JSON:\n{text[:300]}")


def generate_poem(category=None):
    category = category or random.choice(POEM_CATEGORIES)
    print(f"  Category: {category}")

    prompt = f"""You are a children's poet creating content for a YouTube Shorts channel for kids aged 2-6.

TASK: Write ONE original children's poem in the "{category}" category.

POEM RULES:
- 4-6 lines (SHORT — this is a YouTube Short, 20-40 seconds when spoken)
- Simple vocabulary — a 3-year-old should understand every word
- MUST rhyme (AABB or ABAB pattern)
- Fun, positive, educational
- Use repetition — kids love it ("clap clap clap", "one two three")
- Include sounds/actions when possible ("moo", "quack", "jump!")

VISUAL DESCRIPTIONS:
- For EACH line of the poem, write a visual scene description
- These will be used to generate AI images for the video
- Style: "Cute cartoon [subject], bright [color] background, children's book illustration style, adorable, happy, colorful, 2D digital art"
- Keep it child-safe and colorful

YOUTUBE SEO:
- Title: catchy, under 60 chars, include the topic, end with #Shorts
- Description: 3-4 lines, educational angle, include what kids will learn
- Tags: 15 relevant tags (plain text, no #)

Respond ONLY in this exact JSON:
{{
    "category": "{category}",
    "poem_title": "The name of the poem",
    "poem_lines": [
        "First line of the poem",
        "Second line of the poem",
        "Third line of the poem",
        "Fourth line of the poem"
    ],
    "visual_descriptions": [
        "Visual description for line 1 — cartoon style, bright colors",
        "Visual description for line 2 — cartoon style, bright colors",
        "Visual description for line 3 — cartoon style, bright colors",
        "Visual description for line 4 — cartoon style, bright colors"
    ],
    "youtube_title": "Catchy title under 60 chars #Shorts",
    "description": "Fun description for kids and parents\\n\\nWhat your child will learn:\\n- Point 1\\n- Point 2",
    "tags": ["kids poems", "nursery rhymes", "... 15 total"],
    "color_palette": "warm"
}}

ONLY JSON. No other text."""

    text = ask_gemini(prompt)
    data = parse_json_safe(text, retries=2, prompt=prompt)

    # Inject subscribe CTA + default tags
    desc = data.get("description", "")
    desc += f"\n\n🔔 Subscribe to @{CHANNEL_NAME} for daily poems and rhymes!"
    desc += "\n\n#Shorts #KidsPoems #NurseryRhymes #ChildrenSongs #LearnWithFun"
    data["description"] = desc

    tags = data.get("tags", [])
    existing = {t.lower() for t in tags}
    for dt in DEFAULT_TAGS:
        if dt.lower() not in existing:
            tags.append(dt)
            existing.add(dt.lower())
    data["tags"] = tags[:30]

    # Cache the generated poem
    os.makedirs(os.path.join(POEMS_FOLDER, "generated"), exist_ok=True)
    cache_file = os.path.join(
        POEMS_FOLDER, "generated",
        f"{category}_{int(time.time())}.json"
    )
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


def main():
    print("=" * 50)
    print(f"  Kids Poem Generator — {GEMINI_MODEL}")
    print("=" * 50)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    category = random.choice(POEM_CATEGORIES)
    print(f"\n  Generating {category} poem...")
    poem = generate_poem(category)

    print(f"\n  Title: {poem['youtube_title']}")
    print(f"  Lines: {len(poem['poem_lines'])}")
    print(f"  Tags : {len(poem['tags'])}")

    print("\n  Poem:")
    for line in poem["poem_lines"]:
        print(f"    {line}")

    # Save for pipeline
    with open(os.path.join(OUTPUT_FOLDER, "poem_data.json"), "w", encoding="utf-8") as f:
        json.dump(poem, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: assets/output/poem_data.json")
    print("=" * 50)


if __name__ == "__main__":
    main()
